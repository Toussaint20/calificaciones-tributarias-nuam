# core/views.py (Versión robusta)

import pandas as pd
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from .models import Emisor, EventoCorporativo, CalificacionTributaria, ConceptoFactor, DetalleFactor
from django.shortcuts import get_object_or_404

@login_required
def upload_file_view(request):
    if request.method == 'POST':
        archivo = request.FILES.get('archivo_excel')
        
        if not archivo or not archivo.name.lower().endswith('.xlsx'):
            messages.error(request, "Por favor adjunta un archivo con formato .xlsx")
            return redirect('core:upload_file')

        try:
            df = pd.read_excel(archivo, engine='openpyxl')
            df.columns = df.columns.str.strip()

            # --- NUEVA VALIDACIÓN DE COLUMNAS ---
            # Verificamos que las columnas obligatorias existan en el archivo
            columnas_obligatorias = ['Instrumento', 'Numero de dividendo', 'Ejercicio', 'Fecha']
            for col in columnas_obligatorias:
                if col not in df.columns:
                    raise ValueError(f"El archivo no tiene la columna obligatoria: '{col}'")
            # --- FIN DE LA VALIDACIÓN ---

            registros_creados = 0
            with transaction.atomic():
                for index, row in df.iterrows():
                    # (El resto del código sigue igual que antes)
                    # ...
                    suma_factores_credito = 0
                    for i in range(8, 20):
                        col_name = f'Factor {i}'
                        if col_name in df.columns:
                            valor_celda = pd.to_numeric(row.get(col_name), errors='coerce') or 0
                            suma_factores_credito += valor_celda
                    
                    if suma_factores_credito > 1.000001:
                        raise ValueError(f"Fila {index + 2}: La suma de factores 8-19 ({suma_factores_credito}) excede 1.")

                    tipo_soc_raw = str(row.get('Tipo sociedad', 'A')).upper()
                    tipo_soc = 'C' if 'CERRADA' in tipo_soc_raw or 'C' == tipo_soc_raw else 'A'
                    
                    emisor, _ = Emisor.objects.get_or_create(
                        nemonico=row['Instrumento'],
                        defaults={ 'rut': row.get('RUT', f"SIN-RUT-{index}"), 'razon_social': row['Instrumento'], 'tipo_sociedad': tipo_soc }
                    )

                    evento, created = EventoCorporativo.objects.get_or_create(
                        emisor=emisor,
                        numero_dividendo=row['Numero de dividendo'],
                        ejercicio_comercial=row['Ejercicio'],
                        defaults={ 'mercado': row.get('Mercado', 'ACN'), 'fecha_pago': row['Fecha'], 'secuencia': row.get('Secuencia', 0), 'creado_por': request.user }
                    )

                    calificacion, _ = CalificacionTributaria.objects.update_or_create(
                        evento=evento,
                        defaults={ 'monto_unitario_pesos': row.get('Monto Unitario', 0), 'estado': 'BORRADOR', 'modificado_por': request.user }
                    )

                    for col_name in df.columns:
                        if str(col_name).strip().startswith('Factor '):
                            try:
                                num_col = int(col_name.split(' ')[1])
                                valor = row[col_name]
                                if pd.notna(valor) and valor != '':
                                    concepto, _ = ConceptoFactor.objects.get_or_create(
                                        columna_dj=num_col, defaults={'descripcion': f'Factor Columna {num_col}'}
                                    )
                                    DetalleFactor.objects.update_or_create(
                                        calificacion=calificacion, concepto=concepto, defaults={'valor': valor}
                                    )
                            except (ValueError, IndexError):
                                continue
                    
                    if created:
                        registros_creados += 1

            messages.success(request, f"Carga exitosa: Se procesaron y crearon {registros_creados} nuevos eventos correctamente.")
            
        except ValueError as e:
            messages.error(request, f"Error de validación: {str(e)}")
        except Exception as e:
            messages.error(request, f"Error crítico procesando el archivo: {str(e)}")
            
    return render(request, 'core/upload.html')
# core/views.py

@login_required
def mantenedor_view(request):
    # 1. Obtener todas las calificaciones como base
    calificaciones = CalificacionTributaria.objects.select_related('evento__emisor').all()

    # 2. Aplicar filtros si vienen en la URL (método GET)
    filtro_mercado = request.GET.get('mercado', '')
    filtro_instrumento = request.GET.get('instrumento', '')
    filtro_periodo = request.GET.get('periodo', '')

    if filtro_mercado:
        calificaciones = calificaciones.filter(evento__mercado=filtro_mercado)
    
    if filtro_instrumento:
        # Usamos __icontains para buscar texto que contenga el string (insensible a mayúsculas)
        calificaciones = calificaciones.filter(evento__emisor__nemonico__icontains=filtro_instrumento)

    if filtro_periodo:
        calificaciones = calificaciones.filter(evento__ejercicio_comercial=filtro_periodo)

    # 3. Pasar los datos filtrados y los valores de los filtros a la plantilla
    context = {
        'calificaciones': calificaciones,
        'filtro_mercado': filtro_mercado,
        'filtro_instrumento': filtro_instrumento,
        'filtro_periodo': filtro_periodo,
    }
    
    return render(request, 'core/mantenedor.html', context)
@login_required
def create_calificacion_view(request):
    emisores = Emisor.objects.all().order_by('nemonico')
    conceptos = ConceptoFactor.objects.all()

    if request.method == 'POST':
        try:
            with transaction.atomic():
                # --- 1. Crear el Evento Corporativo ---
                emisor_id = request.POST.get('emisor')
                emisor = get_object_or_404(Emisor, pk=emisor_id)
                
                evento = EventoCorporativo.objects.create(
                    emisor=emisor,
                    mercado=request.POST.get('mercado'),
                    fecha_pago=request.POST.get('fecha_pago'),
                    numero_dividendo=request.POST.get('numero_dividendo'),
                    ejercicio_comercial=request.POST.get('ejercicio_comercial'),
                    secuencia=0, # Asignar un valor por defecto o lógica de negocio
                    creado_por=request.user
                )

                # --- 2. Crear la Calificación Tributaria asociada ---
                calificacion = CalificacionTributaria.objects.create(
                    evento=evento,
                    monto_unitario_pesos=request.POST.get('monto_unitario_pesos'),
                    estado=request.POST.get('estado'),
                    modificado_por=request.user
                )

                # --- 3. Guardar los Factores ---
                for concepto in conceptos:
                    valor_factor = request.POST.get(f'factor_{concepto.pk}')
                    if valor_factor is not None and valor_factor != '':
                        DetalleFactor.objects.create(
                            calificacion=calificacion,
                            concepto=concepto,
                            valor=valor_factor
                        )
                
            messages.success(request, f"Calificación para '{evento}' creada exitosamente.")
            return redirect('core:mantenedor')
        except Exception as e:
            messages.error(request, f"Error al crear la calificación: {e}")

    context = {
        'emisores': emisores,
        'conceptos': conceptos,
        'estado_choices': CalificacionTributaria.ESTADO_CHOICES,
    }
    return render(request, 'core/create_calificacion.html', context)

@login_required
def delete_calificacion_view(request, pk):
    # Usamos get_object_or_404 para buscar la calificación.
    # Si no la encuentra, automáticamente muestra una página de "No Encontrado" (Error 404).
    calificacion = get_object_or_404(CalificacionTributaria, pk=pk)

    # Solo permitimos la eliminación a través de una petición POST por seguridad.
    # Esto evita que se pueda borrar algo accidentalmente solo visitando una URL.
    if request.method == 'POST':
        # Guardamos el nombre del evento para el mensaje antes de borrarlo
        evento_info = str(calificacion.evento)
        calificacion.delete()
        messages.success(request, f"La calificación para '{evento_info}' fue eliminada correctamente.")
    else:
        # Si alguien intenta acceder por GET, no hacemos nada y solo lo mandamos al mantenedor.
        messages.error(request, "Acción no permitida.")

    return redirect('core:mantenedor')

@login_required
def edit_calificacion_view(request, pk):
    calificacion = get_object_or_404(CalificacionTributaria, pk=pk)
    conceptos = ConceptoFactor.objects.all()

    if request.method == 'POST':
        try:
            with transaction.atomic():
                calificacion.monto_unitario_pesos = request.POST.get('monto_unitario_pesos')
                calificacion.estado = request.POST.get('estado', calificacion.estado)
                calificacion.modificado_por = request.user
                calificacion.save()

                for concepto in conceptos:
                    valor_factor = request.POST.get(f'factor_{concepto.pk}')
                    if valor_factor is not None and valor_factor != '':
                        DetalleFactor.objects.update_or_create(
                            calificacion=calificacion,
                            concepto=concepto,
                            defaults={'valor': valor_factor}
                        )
                    else:
                        # Si el campo se envía vacío, borramos el factor existente
                        DetalleFactor.objects.filter(calificacion=calificacion, concepto=concepto).delete()

            messages.success(request, f"Calificación para '{calificacion.evento}' actualizada correctamente.")
            return redirect('core:mantenedor')
        except Exception as e:
            messages.error(request, f"Error al actualizar la calificación: {e}")

    factores_existentes = {detalle.concepto.pk: detalle.valor for detalle in calificacion.detalles.all()}
    factores_para_template = []
    for concepto in conceptos:
        factores_para_template.append({
            'concepto': concepto,
            'valor': factores_existentes.get(concepto.pk, '')  # Usamos .get() para evitar errores si no existe
        })

    context = {
        'calificacion': calificacion,
        'factores_para_template': factores_para_template, # Pasamos la nueva lista al template
        'estado_choices': CalificacionTributaria.ESTADO_CHOICES,
    }
    
    return render(request, 'core/edit_calificacion.html', context)
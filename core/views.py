# core/views.py

import pandas as pd
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from .models import Emisor, EventoCorporativo, CalificacionTributaria, ConceptoFactor, DetalleFactor
from .decorators import group_required

# Vista Principal: Mantenedor
@login_required
def mantenedor_view(request):
    calificaciones = CalificacionTributaria.objects.select_related('evento__emisor').all()

    # Lógica de filtros
    filtro_mercado = request.GET.get('mercado', '')
    filtro_instrumento = request.GET.get('instrumento', '')
    filtro_periodo = request.GET.get('periodo', '')

    if filtro_mercado:
        calificaciones = calificaciones.filter(evento__mercado=filtro_mercado)
    if filtro_instrumento:
        calificaciones = calificaciones.filter(evento__emisor__nemonico__icontains=filtro_instrumento)
    if filtro_periodo:
        calificaciones = calificaciones.filter(evento__ejercicio_comercial=filtro_periodo)

    # **CORRECCIÓN CLAVE:**
    # Pasamos los grupos del usuario a la plantilla para que sepa qué botones mostrar.
    context = {
        'calificaciones': calificaciones,
        'filtro_mercado': filtro_mercado,
        'filtro_instrumento': filtro_instrumento,
        'filtro_periodo': filtro_periodo,
        'user_groups': request.user.groups.values_list('name', flat=True)
    }
    
    return render(request, 'core/mantenedor.html', context)

# Vista de Carga Masiva
@login_required
@group_required(['Corredor de Bolsa', 'Analista Tributario'])
def upload_file_view(request):
    if request.method == 'POST':
        archivo = request.FILES.get('archivo_excel')
        
        if not archivo or not archivo.name.lower().endswith('.xlsx'):
            messages.error(request, "Por favor adjunta un archivo con formato .xlsx")
            return redirect('core:upload_file')

        try:
            df = pd.read_excel(archivo, engine='openpyxl')
            df.columns = df.columns.str.strip()
            
            columnas_obligatorias = ['Instrumento', 'Numero de dividendo', 'Ejercicio', 'Fecha']
            for col in columnas_obligatorias:
                if col not in df.columns:
                    raise ValueError(f"El archivo no tiene la columna obligatoria: '{col}'")

            registros_creados = 0
            with transaction.atomic():
                for index, row in df.iterrows():
                    # (Lógica de procesamiento de cada fila...)
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

# Vista de Creación Manual
@login_required
@group_required(['Analista Tributario'])
def create_calificacion_view(request):
    emisores = Emisor.objects.all().order_by('nemonico')
    conceptos = ConceptoFactor.objects.all()

    if request.method == 'POST':
        try:
            with transaction.atomic():
                emisor_id = request.POST.get('emisor')
                emisor = get_object_or_404(Emisor, pk=emisor_id)
                
                evento = EventoCorporativo.objects.create(
                    emisor=emisor,
                    mercado=request.POST.get('mercado'),
                    fecha_pago=request.POST.get('fecha_pago'),
                    numero_dividendo=request.POST.get('numero_dividendo'),
                    ejercicio_comercial=request.POST.get('ejercicio_comercial'),
                    secuencia=0,
                    creado_por=request.user
                )

                calificacion = CalificacionTributaria.objects.create(
                    evento=evento,
                    monto_unitario_pesos=request.POST.get('monto_unitario_pesos'),
                    estado=request.POST.get('estado'),
                    modificado_por=request.user
                )

                for concepto in conceptos:
                    valor_factor = request.POST.get(f'factor_{concepto.pk}')
                    if valor_factor is not None and valor_factor != '':
                        DetalleFactor.objects.create(
                            calificacion=calificacion,
                            concepto=concepto,
                            valor=valor_factor
                        )
                
            messages.success(request, f"Calificacion para '{evento}' creada exitosamente.")
            return redirect('core:mantenedor')
        except Exception as e:
            messages.error(request, f"Error al crear la calificación: {e}")

    context = {
        'emisores': emisores,
        'conceptos': conceptos,
        'estado_choices': CalificacionTributaria.ESTADO_CHOICES,
    }
    return render(request, 'core/create_calificacion.html', context)

# Vista de Edición
@login_required
@group_required(['Analista Tributario'])
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
            'valor': factores_existentes.get(concepto.pk, '')
        })

    context = {
        'calificacion': calificacion,
        'factores_para_template': factores_para_template,
        'estado_choices': CalificacionTributaria.ESTADO_CHOICES,
    }
    
    return render(request, 'core/edit_calificacion.html', context)

# Vista de Eliminación
@login_required
@group_required(['Analista Tributario'])
def delete_calificacion_view(request, pk):
    calificacion = get_object_or_404(CalificacionTributaria, pk=pk)
    if request.method == 'POST':
        evento_info = str(calificacion.evento)
        calificacion.delete()
        messages.success(request, f"La calificación para '{evento_info}' fue eliminada correctamente.")
    else:
        messages.error(request, "Acción no permitida.")
    return redirect('core:mantenedor')

# Vista de Historial (Auditoría)
@login_required
@group_required(['Auditor Interno', 'Analista Tributario'])
def history_calificacion_view(request, pk):
    calificacion = get_object_or_404(CalificacionTributaria, pk=pk)
    historical_records = calificacion.history.select_related('history_user').all()

    context = {
        'calificacion': calificacion,
        'historical_records': historical_records,
    }
    return render(request, 'core/history_calificacion.html', context)
# core/views.py

import pandas as pd
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.db import transaction
from .models import Emisor, EventoCorporativo, CalificacionTributaria, ConceptoFactor, DetalleFactor, AuditLog
from .decorators import group_required
from .forms import EventoForm, CalificacionForm
from django_filters.views import FilterView
from .filters import AuditLogFilter
from django.utils.decorators import method_decorator

# Vista Principal: Mantenedor

@login_required
def mantenedor_view(request):
    # Optimizamos la consulta para traer todo junto
    calificaciones = CalificacionTributaria.objects.select_related('evento__emisor').prefetch_related('detalles__concepto').all()

    # Filtros
    filtro_mercado = request.GET.get('mercado', '')
    filtro_instrumento = request.GET.get('instrumento', '')
    filtro_periodo = request.GET.get('periodo', '')

    if filtro_mercado: calificaciones = calificaciones.filter(evento__mercado=filtro_mercado)
    if filtro_instrumento: calificaciones = calificaciones.filter(evento__emisor__nemonico__icontains=filtro_instrumento)
    if filtro_periodo: calificaciones = calificaciones.filter(evento__ejercicio_comercial=filtro_periodo)

    # --- PREPARACIÓN DE DATOS PARA TABLA SCROLLABLE ---
    tabla_completa = []
    columnas_indices = list(range(8, 38)) # Columnas 8 a 37

    for cal in calificaciones:
        # Convertimos los detalles en un diccionario para acceso rápido
        factores_dict = {d.concepto.columna_dj: d.valor for d in cal.detalles.all()}
        
        # Creamos la lista ordenada de valores
        valores_factores = []
        for col in columnas_indices:
            valores_factores.append(factores_dict.get(col, 0)) # Si no existe, pone 0

        tabla_completa.append({
            'obj': cal,
            'factores': valores_factores
        })

    context = {
        'tabla_completa': tabla_completa, # Usamos esta lista procesada
        'columnas_indices': columnas_indices,
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

            # Validación de columnas
            columnas_obligatorias = ['Instrumento', 'Numero de dividendo', 'Ejercicio', 'Fecha']
            missing = [col for col in columnas_obligatorias if col not in df.columns]
            if missing:
                messages.error(request, f"Faltan columnas obligatorias: {', '.join(missing)}")
                return redirect('core:upload_file')

            registros_creados = 0
            registros_procesados = 0
            errores_acumulados = [] # <--- LISTA PARA GUARDAR TODOS LOS ERRORES

            # Usamos atomic para que si hay errores, no se guarde NADA del archivo
            with transaction.atomic():
                for index, row in df.iterrows():
                    fila_excel = index + 2
                    errores_fila = []

                    # --- A. Validaciones de Negocio ---
                    suma_factores = 0
                    for i in range(8, 20):
                        col_name = f'Factor {i}'
                        if col_name in df.columns:
                            val = pd.to_numeric(row.get(col_name), errors='coerce')
                            if pd.isna(val): val = 0.0
                            if val < 0: 
                                errores_fila.append(f"Factor {i} es negativo")
                            suma_factores += val
                    
                    if suma_factores > 1.000001:
                        errores_fila.append(f"Suma factores 8-19 excede 1 ({suma_factores:.4f})")

                    monto = pd.to_numeric(row.get('Monto Unitario', 0), errors='coerce')
                    if pd.isna(monto): monto = 0
                    if monto < 0: 
                        errores_fila.append("Monto negativo")

                    # Si la fila tiene errores, los guardamos y pasamos a la siguiente
                    if errores_fila:
                        errores_acumulados.append(f"Fila {fila_excel}: {', '.join(errores_fila)}")
                        continue 

                    # --- B. Procesamiento (Solo si no hay errores en la fila) ---
                    try:
                        tipo_soc = 'C' if 'CERRADA' in str(row.get('Tipo sociedad', 'A')).upper() else 'A'
                        
                        emisor, _ = Emisor.objects.get_or_create(
                            nemonico=row['Instrumento'],
                            defaults={'rut': row.get('RUT', f"SIN-RUT-{index}"), 'razon_social': row['Instrumento'], 'tipo_sociedad': tipo_soc}
                        )

                        evento, ev_created = EventoCorporativo.objects.get_or_create(
                            emisor=emisor,
                            numero_dividendo=row['Numero de dividendo'],
                            ejercicio_comercial=row['Ejercicio'],
                            defaults={'mercado': row.get('Mercado', 'ACN'), 'fecha_pago': row['Fecha'], 'secuencia': row.get('Secuencia', 0), 'creado_por': request.user}
                        )

                        calif, cal_created = CalificacionTributaria.objects.update_or_create(
                            evento=evento,
                            defaults={'monto_unitario_pesos': monto, 'estado': 'BORRADOR', 'modificado_por': request.user}
                        )

                        # Factores
                        for col in df.columns:
                            if col.startswith('Factor '):
                                try:
                                    num = int(col.split(' ')[1])
                                    val = pd.to_numeric(row[col], errors='coerce') or 0.0
                                    if val < 0: continue # Ya validado arriba
                                    
                                    # Optimización: Solo guardamos si el concepto existe
                                    if ConceptoFactor.objects.filter(columna_dj=num).exists():
                                        DetalleFactor.objects.update_or_create(
                                            calificacion=calif,
                                            concepto_id=ConceptoFactor.objects.get(columna_dj=num).id,
                                            defaults={'valor': val}
                                        )
                                except: continue

                        registros_procesados += 1
                        if ev_created or cal_created: registros_creados += 1

                    except Exception as e:
                        errores_acumulados.append(f"Fila {fila_excel}: Error técnico ({str(e)})")

                # --- DECISIÓN FINAL ---
                if errores_acumulados:
                    # Si hubo errores, cancelamos TODO (Rollback)
                    transaction.set_rollback(True)
                    
                    # Preparamos mensaje HTML limpio
                    msg = "<strong>La carga falló por los siguientes errores:</strong><br><ul class='mb-0'>"
                    # Mostramos solo los primeros 10 errores para no saturar la pantalla
                    for err in errores_acumulados[:10]:
                        msg += f"<li>{err}</li>"
                    if len(errores_acumulados) > 10:
                        msg += f"<li>... y {len(errores_acumulados)-10} errores más.</li>"
                    msg += "</ul>"
                    
                    messages.error(request, msg, extra_tags='safe') # 'safe' permite renderizar HTML
                else:
                    if registros_creados > 0:
                        messages.success(request, f"Carga exitosa: {registros_procesados} registros procesados ({registros_creados} nuevos).")
                    else:
                        messages.info(request, f"Carga completa: {registros_procesados} registros actualizados.")

        except Exception as e:
            messages.error(request, f"Error crítico: {str(e)}")
            
    return render(request, 'core/upload.html')

# Vista de Creación Manual
@login_required
@group_required(['Analista Tributario'])
def create_calificacion_view(request):
    conceptos = ConceptoFactor.objects.all()

    if request.method == 'POST':
        form_evento = EventoForm(request.POST)
        form_calificacion = CalificacionForm(request.POST)

        if form_evento.is_valid() and form_calificacion.is_valid():
            try:
                with transaction.atomic():
                    # --- 1. VALIDACIÓN DE NEGOCIO (Suma de Créditos) ---
                    suma_creditos = 0
                    # Recorremos los conceptos que corresponden a columnas 8 a 19
                    for concepto in conceptos:
                        if 8 <= concepto.columna_dj <= 19:
                            valor_raw = request.POST.get(f'factor_{concepto.pk}')
                            if valor_raw:
                                try:
                                    suma_creditos += float(valor_raw)
                                except ValueError:
                                    pass # El error de tipo se captura abajo individualmente
                    
                    # Verificamos la suma (con margen de error epsilon)
                    if suma_creditos > 1.000001:
                        raise ValueError(f"La suma de los factores de crédito (Col 8 a 19) es {suma_creditos:.4f}. No puede exceder 1.")

                    # --- 2. Guardado de Datos ---
                    evento = form_evento.save(commit=False)
                    evento.creado_por = request.user
                    evento.secuencia = 0 
                    evento.save()

                    calificacion = form_calificacion.save(commit=False)
                    calificacion.evento = evento
                    calificacion.modificado_por = request.user
                    calificacion.save()

                    # --- 3. Procesar Factores Individuales ---
                    for concepto in conceptos:
                        valor_raw = request.POST.get(f'factor_{concepto.pk}')
                        
                        if valor_raw and valor_raw.strip() != '':
                            try:
                                valor_float = float(valor_raw)
                                if valor_float < 0:
                                    raise ValueError(f"El factor '{concepto.descripcion}' no puede ser negativo.")
                                
                                DetalleFactor.objects.create(
                                    calificacion=calificacion,
                                    concepto=concepto,
                                    valor=valor_float
                                )
                            except ValueError as ve:
                                if "could not convert string" in str(ve):
                                    raise ValueError(f"El valor para '{concepto.descripcion}' no es válido.")
                                raise ve 

                messages.success(request, "Calificación creada exitosamente.")
                return redirect('core:mantenedor')

            except ValueError as ve:
                messages.error(request, f"Error de validación: {ve}")
            except Exception as e:
                messages.error(request, f"Error técnico al guardar: {e}")
        else:
            messages.error(request, "Por favor corrija los errores en el formulario.")
    
    else:
        form_evento = EventoForm()
        form_calificacion = CalificacionForm()

    context = {
        'form_evento': form_evento,
        'form_calificacion': form_calificacion,
        'conceptos': conceptos,
    }
    return render(request, 'core/create_calificacion.html', context)

# Vista de Edición
@login_required
@group_required(['Analista Tributario'])
def edit_calificacion_view(request, pk):
    calificacion = get_object_or_404(CalificacionTributaria, pk=pk)
    evento = calificacion.evento
    conceptos = ConceptoFactor.objects.all()

    if request.method == 'POST':
        form_evento = EventoForm(request.POST, instance=evento)
        form_calificacion = CalificacionForm(request.POST, instance=calificacion)

        if form_evento.is_valid() and form_calificacion.is_valid():
            try:
                with transaction.atomic():
                    # --- 1. VALIDACIÓN DE NEGOCIO (Suma de Créditos 8-19) ---
                    suma_creditos = 0
                    for concepto in conceptos:
                        if 8 <= concepto.columna_dj <= 19:
                            valor_raw = request.POST.get(f'factor_{concepto.pk}')
                            if valor_raw and valor_raw.strip():
                                try:
                                    suma_creditos += float(valor_raw)
                                except ValueError:
                                    pass 
                    
                    if suma_creditos > 1.000001:
                        raise ValueError(f"La suma de los factores 8 al 19 es {suma_creditos:.4f}. No puede exceder 1.")

                    # --- 2. Guardado de Forms ---
                    form_evento.save()
                    
                    calif = form_calificacion.save(commit=False)
                    calif.modificado_por = request.user
                    calif.save()

                    # --- 3. Guardado de Factores ---
                    for concepto in conceptos:
                        valor_raw = request.POST.get(f'factor_{concepto.pk}')
                        
                        if valor_raw and valor_raw.strip() != '':
                            try:
                                valor_float = float(valor_raw)
                                if valor_float < 0:
                                    raise ValueError(f"El factor {concepto.columna_dj} no puede ser negativo.")
                                
                                DetalleFactor.objects.update_or_create(
                                    calificacion=calificacion,
                                    concepto=concepto,
                                    defaults={'valor': valor_float}
                                )
                            except ValueError as ve:
                                if "could not convert string" in str(ve):
                                    raise ValueError(f"El valor para Factor {concepto.columna_dj} no es válido.")
                                raise ve
                        else:
                            DetalleFactor.objects.filter(calificacion=calificacion, concepto=concepto).delete()

                messages.success(request, "Calificación actualizada correctamente.")
                return redirect('core:mantenedor')

            except ValueError as ve:
                messages.error(request, f"Error de validación: {ve}")
            except Exception as e:
                messages.error(request, f"Error técnico: {e}")
        else:
            messages.error(request, "Corrija los errores en los datos generales.")
    
    else:
        form_evento = EventoForm(instance=evento)
        form_calificacion = CalificacionForm(instance=calificacion)

    # Preparamos datos para la plantilla
    factores_existentes = {d.concepto.pk: d.valor for d in calificacion.detalles.all()}
    factores_para_template = []
    for concepto in conceptos:
        factores_para_template.append({
            'concepto': concepto,
            'valor': factores_existentes.get(concepto.pk, '')
        })

    context = {
        'calificacion': calificacion,
        'form_evento': form_evento,
        'form_calificacion': form_calificacion,
        'factores_para_template': factores_para_template,
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

# log de auditoria
@method_decorator(group_required(['Auditor Interno', 'Administrador']), name='dispatch')
class AuditLogListView(LoginRequiredMixin, FilterView):
    model = AuditLog
    template_name = 'core/audit_log_list.html'
    context_object_name = 'logs'
    paginate_by = 20
    ordering = ['-timestamp']
    
    # Conectamos el filtro a la vista
    filterset_class = AuditLogFilter

    def get_queryset(self):
        # Mantenemos la optimización de base de datos
        return super().get_queryset().select_related('user', 'content_type')
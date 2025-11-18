# core/admin.py

from django.contrib import admin
from simple_history.admin import SimpleHistoryAdmin
from .models import Emisor, EventoCorporativo, CalificacionTributaria, ConceptoFactor, DetalleFactor

# Configuración para ver los factores "dentro" de la calificación
class DetalleFactorInline(admin.TabularInline):
    model = DetalleFactor
    extra = 0 # No mostrar filas vacías extra
    autocomplete_fields = ['concepto']

@admin.register(Emisor)
class EmisorAdmin(SimpleHistoryAdmin):
    list_display = ('rut', 'nemonico', 'razon_social', 'tipo_sociedad')
    search_fields = ('rut', 'nemonico', 'razon_social')
    
@admin.register(ConceptoFactor)
class ConceptoFactorAdmin(admin.ModelAdmin):
    list_display = ('columna_dj', 'descripcion')
    ordering = ('columna_dj',)
    search_fields = ('descripcion', 'columna_dj')
    
@admin.register(EventoCorporativo)
class EventoCorporativoAdmin(SimpleHistoryAdmin):
    list_display = ('emisor', 'fecha_pago', 'numero_dividendo', 'mercado', 'ejercicio_comercial')
    list_filter = ('mercado', 'ejercicio_comercial')
    search_fields = ('emisor__nemonico', 'emisor__rut')
    
@admin.register(CalificacionTributaria)
class CalificacionTributariaAdmin(SimpleHistoryAdmin):
    list_display = ('evento', 'monto_unitario_pesos', 'estado', 'ultima_modificacion')
    list_filter = ('estado',)
    search_fields = ('evento__emisor__nemonico',)
    inlines = [DetalleFactorInline] 
# core/admin.py

from django.contrib import admin
from simple_history.admin import SimpleHistoryAdmin
from .models import Emisor, EventoCorporativo, CalificacionTributaria, ConceptoFactor, DetalleFactor, AuditLog

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
    

@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    # Campos que se ven en la lista
    list_display = ('action', 'get_content_type', 'object_repr', 'user', 'timestamp')
    
    # Filtros laterales
    list_filter = ('action', 'timestamp', 'content_type')
    
    # Buscador
    search_fields = ('object_id', 'user__username', 'changes')
    
    # Campos de solo lectura
    readonly_fields = ('user', 'action', 'content_type', 'object_id', 'object_repr', 'changes', 'timestamp')

    def has_add_permission(self, request):
        return False  # Nadie puede crear logs manualmente

    def has_delete_permission(self, request, obj=None):
        return False  # Nadie puede borrar logs

    # --- DEFINICIONES DE CAMPOS CALCULADOS ---

    # 1. Función para obtener la representación del objeto (nombre)
    def object_repr(self, obj):
        if obj.content_object:
            return str(obj.content_object)
        return f"Objeto eliminado (ID: {obj.object_id})"
    object_repr.short_description = 'Objeto Afectado'

    # 2. Función para mostrar el tipo de contenido más limpio (opcional)
    def get_content_type(self, obj):
        return obj.content_type.model
    get_content_type.short_description = 'Modelo'
# core/filters.py
import django_filters
from .models import CalificacionTributaria

class AuditoriaFilter(django_filters.FilterSet):
    # Filtro por rango de fechas
    start_date = django_filters.DateFilter(field_name='history_date', lookup_expr='gte', label='Desde')
    end_date = django_filters.DateFilter(field_name='history_date', lookup_expr='lte', label='Hasta')
    # Filtro por usuario (texto parcial)
    usuario = django_filters.CharFilter(field_name='history_user__username', lookup_expr='icontains', label='Usuario')
    # Filtro por instrumento
    instrumento = django_filters.CharFilter(field_name='evento__emisor__nemonico', lookup_expr='icontains', label='Instrumento')

    class Meta:
        model = CalificacionTributaria.history.model # Modelo histórico
        fields = ['history_type'] # Filtro extra por tipo (Creación/Edición/Borrado)
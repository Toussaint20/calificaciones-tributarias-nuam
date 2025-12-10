# /app/core/filters.py
import django_filters
from django import forms
from .models import AuditLog

class AuditLogFilter(django_filters.FilterSet):
    # Definimos las opciones manualmente aquí para evitar el error de atributo
    ACTION_CHOICES = [
        ('CREATE', 'Creación'),
        ('UPDATE', 'Edición'),
        ('DELETE', 'Eliminación'),
    ]

    username = django_filters.CharFilter(
        field_name='user__username', 
        lookup_expr='icontains', 
        label='Usuario'
    )
    
    action = django_filters.ChoiceFilter(choices=ACTION_CHOICES, label='Acción')

    start_date = django_filters.DateFilter(
        field_name='timestamp', 
        lookup_expr='gte', 
        label='Fecha Desde',
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    end_date = django_filters.DateFilter(
        field_name='timestamp', 
        lookup_expr='lte', 
        label='Fecha Hasta',
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )

    class Meta:
        model = AuditLog
        fields = ['username', 'action', 'start_date', 'end_date']
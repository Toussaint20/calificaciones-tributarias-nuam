from django import forms
from .models import EventoCorporativo, CalificacionTributaria

class EstiloBootstrapMixin:
    """Mixin para añadir clases de Bootstrap a todos los campos"""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            # Si es Checkbox usa form-check-input, si no, form-control
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs['class'] = 'form-check-input'
            else:
                field.widget.attrs['class'] = 'form-control'

class EventoForm(EstiloBootstrapMixin, forms.ModelForm):
    class Meta:
        model = EventoCorporativo
        fields = ['emisor', 'mercado', 'ejercicio_comercial', 'numero_dividendo', 'fecha_pago']
        widgets = {
            'fecha_pago': forms.DateInput(attrs={'type': 'date'}),
            'ejercicio_comercial': forms.NumberInput(attrs={'placeholder': 'Ej: 2025'}),
        }
        labels = {
            'numero_dividendo': 'N° Dividendo',
        }

class CalificacionForm(EstiloBootstrapMixin, forms.ModelForm):
    class Meta:
        model = CalificacionTributaria
        fields = ['monto_unitario_pesos'] # Solo el monto, los factores los manejamos manual
        labels = {
            'monto_unitario_pesos': 'Monto Unitario ($)',
        }
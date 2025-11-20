# core/forms.py

from django import forms
from .models import EventoCorporativo, CalificacionTributaria

class EventoForm(forms.ModelForm):
    class Meta:
        model = EventoCorporativo
        fields = ['emisor', 'mercado', 'fecha_pago', 'numero_dividendo', 'ejercicio_comercial']
        
        # Personalizamos los widgets para que tengan estilos CSS y calendarios
        widgets = {
            'emisor': forms.Select(attrs={'class': 'form-control'}),
            'mercado': forms.Select(attrs={'class': 'form-control'}),
            'fecha_pago': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'numero_dividendo': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
            'ejercicio_comercial': forms.NumberInput(attrs={'class': 'form-control', 'min': '2000'}),
        }

class CalificacionForm(forms.ModelForm):
    class Meta:
        model = CalificacionTributaria
        fields = ['monto_unitario_pesos', 'estado']
        widgets = {
            'monto_unitario_pesos': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.000001'}),
            'estado': forms.Select(attrs={'class': 'form-control'}),
        }

    # --- VALIDACIÓN PERSONALIZADA (Regla de Negocio) ---
    def clean_monto_unitario_pesos(self):
        monto = self.cleaned_data.get('monto_unitario_pesos')
        if monto is not None and monto < 0:
            raise forms.ValidationError("El monto por acción no puede ser negativo.")
        return monto
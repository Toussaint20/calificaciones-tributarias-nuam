# core/models.py

from django.db import models
from django.contrib.auth.models import User
from simple_history.models import HistoricalRecords

# --- TABLAS MAESTRAS (Catálogos) ---

class Emisor(models.Model):
    rut = models.CharField(max_length=12, unique=True, verbose_name="RUT")
    razon_social = models.CharField(max_length=255)
    nemonico = models.CharField(max_length=20, unique=True, help_text="Ej: COPEC")
    
    TIPO_SOCIEDAD_CHOICES = [('A', 'Abierta'), ('C', 'Cerrada')]
    tipo_sociedad = models.CharField(max_length=1, choices=TIPO_SOCIEDAD_CHOICES, default='A')

    def __str__(self):
        return self.nemonico

class ConceptoFactor(models.Model):
    columna_dj = models.IntegerField(unique=True, help_text="Número de columna en la DJ 1949 (8-37)")
    descripcion = models.CharField(max_length=255)
    tipo_dato = models.CharField(max_length=50, default="Factor (8 decimales)")

    def __str__(self):
        return f"Columna {self.columna_dj}: {self.descripcion}"

    class Meta:
        ordering = ['columna_dj']

# --- TABLAS TRANSACCIONALES ---

class EventoCorporativo(models.Model):
    MERCADO_CHOICES = [
        ('ACN', 'Acciones'),
        ('CFI', 'Cuotas Fondos de Inversión'),
        ('CFM', 'Cuotas Fondos Mutuos'),
    ]

    emisor = models.ForeignKey(Emisor, on_delete=models.PROTECT, db_index=True)
    mercado = models.CharField(max_length=3, choices=MERCADO_CHOICES, default='ACN')
    
    fecha_pago = models.DateField(db_index=True)
    fecha_registro = models.DateField(null=True, blank=True)
    
    # === CAMPOS CORREGIDOS ===
    numero_dividendo = models.PositiveIntegerField(help_text="N° del evento según el emisor", default=0)
    secuencia = models.PositiveIntegerField(help_text="Identificador único de secuencia del archivo", default=0)
    ejercicio_comercial = models.PositiveIntegerField(help_text="Año comercial (Ej: 2023)", default=2024) # Default al año actual es razonable

    creado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    history = HistoricalRecords()

    class Meta:
        unique_together = ('emisor', 'numero_dividendo', 'ejercicio_comercial')
    
    def __str__(self):
        return f"{self.emisor} - Div #{self.numero_dividendo} ({self.ejercicio_comercial})"

class CalificacionTributaria(models.Model):
    # --- CAMBIO IMPORTANTE AQUÍ ---
    # 1. Definimos las opciones como un atributo de la clase.
    ESTADO_CHOICES = [
        ('BORRADOR', 'Borrador'),
        ('EN_REVISION', 'En Revisión'),
        ('VALIDADO', 'Validado'),
        ('RECHAZADO', 'Rechazado'),
    ]

    evento = models.OneToOneField(EventoCorporativo, on_delete=models.CASCADE, related_name='calificacion')
    
    monto_total_distribuido = models.DecimalField(max_digits=20, decimal_places=4, default=0)
    monto_unitario_pesos = models.DecimalField(max_digits=12, decimal_places=6, help_text="Monto $/Acción", default=0)

    # 2. Ahora, el campo 'estado' usa esta variable.
    estado = models.CharField(
        max_length=20, 
        choices=ESTADO_CHOICES, # <--- Referencia a la variable de clase
        default='BORRADOR',
        db_index=True
    )
    
    ultima_modificacion = models.DateTimeField(auto_now=True)
    modificado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    history = HistoricalRecords()

    def __str__(self):
        return f"Calificación {self.evento}"

class DetalleFactor(models.Model):
    calificacion = models.ForeignKey(CalificacionTributaria, on_delete=models.CASCADE, related_name='detalles')
    concepto = models.ForeignKey(ConceptoFactor, on_delete=models.PROTECT)
    
    # === CAMPO CORREGIDO ===
    valor = models.DecimalField(max_digits=10, decimal_places=8, default=0)

    class Meta:
        unique_together = ('calificacion', 'concepto')
# core/models.py

from django.db import models
from django.conf import settings
from django.contrib.auth.models import User
from simple_history.models import HistoricalRecords
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey

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
#Entidad transaccional vinculada por FK
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

#Cabecera de la calificación (1:1 con Evento)
class CalificacionTributaria(models.Model):
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

#Cumple 1FN: Elimina grupos repetidos (factores 8-37)
class DetalleFactor(models.Model):
    calificacion = models.ForeignKey(CalificacionTributaria, on_delete=models.CASCADE, related_name='detalles')
    concepto = models.ForeignKey(ConceptoFactor, on_delete=models.PROTECT)
    
    valor = models.DecimalField(max_digits=10, decimal_places=8, default=0)

    class Meta:
        unique_together = ('calificacion', 'concepto')
        

class AuditLog(models.Model):
    ACTION_TYPES = (
        ('CREATE', 'Creación'),
        ('UPDATE', 'Actualización'),
        ('DELETE', 'Eliminación'),
        ('LOGIN', 'Inicio de Sesión'),
    )

    # Quién
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='audit_logs'
    )
    
    # Cuándo y Qué pasó
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True) # Indexado para filtrar rápido por fecha
    action = models.CharField(max_length=20, choices=ACTION_TYPES)
    
    # Sobre qué objeto (Polimorfismo: permite guardar logs de cualquier modelo: Factores, Usuarios, etc.)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, null=True, blank=True)
    object_id = models.CharField(max_length=255, null=True, blank=True)
    content_object = GenericForeignKey('content_type', 'object_id')
    
    # Detalles técnicos (IP opcional, pero recomendada en tributaria)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    
    # El núcleo: Antes y Después usando JSON de Postgres
    changes = models.JSONField(default=dict, blank=True) 
    # Ejemplo de estructura: {"monto": {"old": 100, "new": 150}}

    class Meta:
        ordering = ['-timestamp']
        verbose_name = 'Registro de Auditoría'
        verbose_name_plural = 'Registros de Auditoría'

    def __str__(self):
        return f"{self.timestamp} - {self.user} - {self.action}"
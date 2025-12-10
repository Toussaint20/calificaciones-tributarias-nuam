from rest_framework import serializers
from .models import Emisor, EventoCorporativo, CalificacionTributaria, DetalleFactor

class EmisorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Emisor
        fields = '__all__'

class EventoCorporativoSerializer(serializers.ModelSerializer):
    emisor = EmisorSerializer(read_only=True) # Para ver el detalle del emisor anidado
    
    class Meta:
        model = EventoCorporativo
        fields = '__all__'

class DetalleFactorSerializer(serializers.ModelSerializer):
    concepto_nombre = serializers.CharField(source='concepto.descripcion', read_only=True)
    columna_dj = serializers.IntegerField(source='concepto.columna_dj', read_only=True)

    class Meta:
        model = DetalleFactor
        fields = ['id', 'concepto_nombre', 'columna_dj', 'valor']

class CalificacionTributariaSerializer(serializers.ModelSerializer):
    evento = EventoCorporativoSerializer(read_only=True)
    # Incluimos los factores detallados dentro de la respuesta
    detalles = DetalleFactorSerializer(many=True, read_only=True)

    class Meta:
        model = CalificacionTributaria
        fields = '__all__'
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from .models import Emisor, EventoCorporativo, CalificacionTributaria
from .serializers import (
    EmisorSerializer, 
    EventoCorporativoSerializer, 
    CalificacionTributariaSerializer
)

class EmisorViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API para listar Emisores (Solo lectura)
    """
    queryset = Emisor.objects.all()
    serializer_class = EmisorSerializer
    permission_classes = [IsAuthenticated]

class EventoViewSet(viewsets.ModelViewSet):
    """
    API para Eventos Corporativos
    """
    queryset = EventoCorporativo.objects.all().order_by('-fecha_pago')
    serializer_class = EventoCorporativoSerializer
    permission_classes = [IsAuthenticated]

class CalificacionViewSet(viewsets.ModelViewSet):
    """
    API principal de Calificaciones Tributarias
    """
    queryset = CalificacionTributaria.objects.select_related('evento__emisor').prefetch_related('detalles__concepto').all().order_by('-evento__fecha_pago')
    serializer_class = CalificacionTributariaSerializer
    permission_classes = [IsAuthenticated]
    
    # Filtros simples (opcional, si quisieras filtrar por URL)
    def get_queryset(self):
        queryset = super().get_queryset()
        nemonico = self.request.query_params.get('nemonico')
        year = self.request.query_params.get('year')
        
        if nemonico:
            queryset = queryset.filter(evento__emisor__nemonico__icontains=nemonico)
        if year:
            queryset = queryset.filter(evento__ejercicio_comercial=year)
            
        return queryset
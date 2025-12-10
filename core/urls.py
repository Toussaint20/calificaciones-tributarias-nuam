# core/urls.py

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from .views import AuditLogListView
from . import api_views
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework.authtoken.views import obtain_auth_token

# Configuración del Router de la API
router = DefaultRouter()
router.register(r'emisores', api_views.EmisorViewSet)
router.register(r'eventos', api_views.EventoViewSet)
router.register(r'calificaciones', api_views.CalificacionViewSet)

app_name = 'core'

urlpatterns = [
    # Ruta para la página principal del mantenedor
    path('', views.mantenedor_view, name='mantenedor'),

    #ruta para crear calificacion
    path('calificacion/new/', views.create_calificacion_view, name='create_calificacion'),
    # Ruta para la carga de archivos
    path('upload/', views.upload_file_view, name='upload_file'),
    #ruta para eliminar
    path('calificacion/<int:pk>/delete/', views.delete_calificacion_view, name='delete_calificacion'),
    #ruta para editar
    path('calificacion/<int:pk>/edit/', views.edit_calificacion_view, name='edit_calificacion'),
    #ruta para historial
    path('calificacion/<int:pk>/history/', views.history_calificacion_view, name='history_calificacion'),
    #ruta para auditoría global
    path('historial/', AuditLogListView.as_view(), name='audit_log_list'),
    # --- URLs DE LA API ---
    path('api/', include(router.urls)),
    path('api/login/', obtain_auth_token, name='api_token_auth'),
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='core:schema'), name='swagger-ui'),
    ]
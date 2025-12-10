# core/urls.py

from django.urls import path
from . import views

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
    path('auditoria/', views.auditoria_global_view, name='auditoria_global'),
]
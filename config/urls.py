# config/urls.py

from django.contrib import admin
from django.urls import path, include # Asegúrate de que 'include' esté importado

urlpatterns = [
    path('admin/', admin.site.urls),
    # Cualquier URL que no sea /admin/ la buscará en core/urls.py
    path('accounts/', include('django.contrib.auth.urls')),
    path('', include('core.urls')),
]
import threading
from django.shortcuts import redirect
from django.urls import reverse
from django_otp.plugins.otp_totp.models import TOTPDevice
from django.utils.cache import add_never_cache_headers

# ==========================================
# 1. LÓGICA DE AUDITORÍA 
# ==========================================

# Crear un almacenamiento local para el hilo
_thread_locals = threading.local()

def get_current_user():
    return getattr(_thread_locals, 'user', None)

class CurrentUserMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Intercepta la request y guarda el usuario en el hilo actual
        _thread_locals.user = request.user
        response = self.get_response(request)
        return response


# ==========================================
# 2. LÓGICA DE SEGURIDAD 2FA 
# ==========================================

class Force2FAMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Rutas permitidas para evitar bucles infinitos
        allowed_paths = [
            '/admin/login/',             # Login de Admin
            '/accounts/login/',          # Login estándar
            '/logout/',                  # Salir
            reverse('core:setup_2fa'),   # Configurar QR
            reverse('core:verify_2fa'),  # Verificar Código
        ]

        # Lógica del Portero:
        if request.user.is_authenticated:
            #para evitar que un usuario acceda al login mientras esté logueado
            if request.path == '/accounts/login/' and request.user.is_verified():
                return redirect('core:mantenedor')
            # Si el usuario NO está verificado con 2FA...
            if not request.user.is_verified():
                
                # Y no está intentando entrar a una ruta permitida...
                # (Usamos startswith para permitir sub-rutas como /static/)
                if request.path not in allowed_paths and not request.path.startswith('/static/'):
                    
                    # Verificamos si tiene un dispositivo configurado
                    has_device = TOTPDevice.objects.filter(user=request.user, confirmed=True).exists()
                    
                    if has_device:
                        # Tiene dispositivo -> A la Aduana (Ingresar código)
                        return redirect('core:verify_2fa')
                    else:
                        # NO tiene dispositivo -> A Configuración (Escanear QR)
                        return redirect('core:setup_2fa')

        response = self.get_response(request)
        return response
    
class NoCacheMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        
        # No aplicamos esto a archivos estáticos (CSS/JS/Imágenes) para no afectar rendimiento
        if not request.path.startswith('/static/'):
            add_never_cache_headers(response)
        
        return response
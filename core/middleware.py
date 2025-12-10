# /app/core/middleware.py
import threading

# Crear un almacenamiento local para el hilo
_thread_locals = threading.local()

# Esta es la función que signals.py está buscando
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
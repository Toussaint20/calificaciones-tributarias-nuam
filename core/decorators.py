# core/decorators.py

from django.core.exceptions import PermissionDenied
from functools import wraps

def group_required(group_names):
    """
    Decorador que comprueba si un usuario pertenece a al menos uno de los grupos especificados.
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if request.user.is_authenticated:
                # Si el usuario es superadmin, tiene acceso a todo
                if request.user.is_superuser:
                    return view_func(request, *args, **kwargs)
                
                # Comprobamos si el usuario pertenece a alguno de los grupos requeridos
                user_groups = set(request.user.groups.values_list('name', flat=True))
                required_groups = set(group_names)
                
                if user_groups.intersection(required_groups):
                    return view_func(request, *args, **kwargs)
            
            # Si no cumple ninguna condición, se niega el acceso.
            raise PermissionDenied
        return _wrapped_view
    return decorator
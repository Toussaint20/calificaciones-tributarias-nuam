from django import template

register = template.Library()

@register.filter(name='has_group')
def has_group(user, group_name):
    """
    Uso en template: {% if request.user|has_group:"Auditor Interno" %}
    """
    if user.is_superuser:
        return True
    return user.groups.filter(name=group_name).exists()

@register.filter(name='lookup_factor')
def lookup_factor(post_data, key):
    """
    Recupera el valor de un factor desde request.POST usando el ID del concepto.
    Uso: {{ request.POST|lookup_factor:concepto.pk }}
    """
    if not post_data:
        return ""
    return post_data.get(f'factor_{key}', "")
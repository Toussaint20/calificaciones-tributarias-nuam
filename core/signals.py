# core/signals.py
import json
from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from django.forms.models import model_to_dict
from django.core.serializers.json import DjangoJSONEncoder
from .models import AuditLog

EXCLUDED_MODELS = ['AuditLog', 'Session']

@receiver(pre_save)
def audit_log_pre_save(sender, instance, **kwargs):
    if sender.__name__ in EXCLUDED_MODELS:
        return

    if instance.pk:
        try:
            current_instance = sender.objects.get(pk=instance.pk)
            instance._old_state = model_to_dict(current_instance)
        except sender.DoesNotExist:
            instance._old_state = {}
    else:
        instance._old_state = {}

@receiver(post_save)
def audit_log_post_save(sender, instance, created, **kwargs):
    if sender.__name__ in EXCLUDED_MODELS:
        return

    from .middleware import get_current_user 
    
    user = get_current_user()
    
    if user and not user.is_authenticated:
        user = None
        
    new_state = model_to_dict(instance)
    changes = {}
    action = 'CREATE' if created else 'UPDATE'

    if action == 'UPDATE' and hasattr(instance, '_old_state'):
        for key, value in new_state.items():
            old_value = instance._old_state.get(key)
            if value != old_value:
                changes[key] = {
                    'old': str(old_value),
                    'new': str(value)
                }
        
        if not changes:
            return
    elif action == 'CREATE':
        changes = {k: {'old': None, 'new': str(v)} for k, v in new_state.items()}

    AuditLog.objects.create(
        user=user,
        action=action,
        content_object=instance,
        changes=json.loads(json.dumps(changes, cls=DjangoJSONEncoder))
    )

@receiver(post_delete)
def audit_log_post_delete(sender, instance, **kwargs):
    if sender.__name__ in EXCLUDED_MODELS:
        return

    from .middleware import get_current_user

    user = get_current_user()
    
    if user and not user.is_authenticated:
        user = None
        
    old_state = model_to_dict(instance)
    
    AuditLog.objects.create(
        user=user,
        action='DELETE',
        content_object=instance,
        changes=json.loads(json.dumps(old_state, cls=DjangoJSONEncoder))
    )
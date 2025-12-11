from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group

class Command(BaseCommand):
    help = 'Crea los grupos de usuarios (Roles) por defecto del sistema.'

    def handle(self, *args, **kwargs):
        grupos_requeridos = [
            'Analista Tributario', 
            'Corredor de Bolsa', 
            'Auditor Interno'
        ]
        
        self.stdout.write('Verificando grupos de usuarios...')

        for nombre_grupo in grupos_requeridos:
            grupo, created = Group.objects.get_or_create(name=nombre_grupo)
            if created:
                self.stdout.write(self.style.SUCCESS(f'✅ Grupo creado: "{nombre_grupo}"'))
            else:
                self.stdout.write(self.style.WARNING(f'ℹ️ El grupo "{nombre_grupo}" ya existía.'))
        
        self.stdout.write(self.style.SUCCESS('¡Proceso de creación de grupos finalizado!'))
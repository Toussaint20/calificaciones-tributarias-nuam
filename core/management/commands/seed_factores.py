# core/management/commands/seed_factores.py

from django.core.management.base import BaseCommand
from django.db import transaction
from core.models import ConceptoFactor

# Lista actualizada según requerimiento del usuario
FACTORES_DJ1949 = [
    (8, "No constitutiva de Renta No Acogido a Impto."),
    (9, "Impto. 1ra Categ. Afecto GI. Comp. Con Devolución"),
    (10, "Impuesto Tasa Adicional Exento Art. 21"),
    (11, "Incremento Impuesto 1ra Categoría"),
    (12, "Impto. 1ra Categ. Exento GI. Comp. Con Devolución"),
    (13, "Impto. 1ra Categ. Afecto GI. Comp. Sin Devolución"),
    (14, "Impto. 1ra Categ. Exento GI. Comp, Sin Devolución"),
    (15, "Impto. Créditos por Impuestos Externos"),
    (16, "No Constitutiva de Renta Acogido a Impto."),
    (17, "No constitutiva de Renta Devolución de Capital Art. 17"),
    (18, "Rentas Exentas de Impto. GC Y/O Impto Adicional"),
    (19, "A Ingreso no Constitutivos de Renta"),
    (20, "Sin Derecho a Devolución"),
    (21, "Con Derecho a Devolución"),
    (22, "Sin Derecho a Devolución"),
    (23, "Con Derecho a Devolución"),
    (24, "Sin derecho a devolución"),
    (25, "Con Derecho a Devolución"),
    (26, "Sin derecho a devolución"),
    (27, "Con Derecho a Devolución"),
    (28, "Crédito por IPE"),
    (29, "Sin derecho a devolución"),
    (30, "Con Derecho a Devolución"),
    (31, "Sin derecho a devolución"),
    (32, "Con Derecho a Devolución"),
    (33, "Crédito por IPE"),
    (34, "Cred. Por Impto. Tasa Adicional, Ex Art 21 LIR"),
    (35, "Tasa Efectiva Del Cred. Del FUT (TEF)"),
    (36, "Tasa Efectiva Del Cred. Del FUNT (TEX)"),
    (37, "Devolución de Capital Art. 17 num 7 LIR"),
]

class Command(BaseCommand):
    help = 'Actualiza la tabla ConceptoFactor con las descripciones personalizadas.'

    @transaction.atomic
    def handle(self, *args, **kwargs):
        self.stdout.write("Actualizando factores...")
        
        for columna, descripcion in FACTORES_DJ1949:
            ConceptoFactor.objects.update_or_create(
                columna_dj=columna,
                defaults={'descripcion': descripcion}
            )
        
        self.stdout.write(self.style.SUCCESS('¡Factores 8-37 actualizados correctamente!'))
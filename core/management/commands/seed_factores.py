# core/management/commands/seed_factores.py

from django.core.management.base import BaseCommand
from django.db import transaction
from core.models import ConceptoFactor

# Lista completa de factores extraídos del documento oficial DJ 1949 de servicio impuestos internos (SII)
FACTORES_DJ1949 = [
   (8, "(8) Crédito por IDPC o IPE, con derecho a devolución, sujeto a restitución"),
    (9, "(9) Crédito por IDPC o IPE, sin derecho a devolución, sujeto a restitución"),
    (10, "(10) Crédito por IDPC, con derecho a devolución, no sujeto a restitución"),
    (11, "(11) Crédito por IDPC, sin derecho a devolución, no sujeto a restitución"),
    (12, "(12) Crédito por impuesto de primera categoría acumulado a imputar"),
    (13, "(13) Crédito por impuesto de primera categoría voluntario a imputar"),
    (14, "(14) Crédito total por IDPC a imputar contra impuestos finales"),
    (15, "(15) Monto de la restitución del crédito por IDPC"),
    (16, "(16) Dividendo o distribución de utilidades afectas (monto incremental)"),
    (17, "(17) Rentas o cantidades afectas a IGC o IA (imputadas al RAP)"),
    (18, "(18) Rentas exentas del IGC, pero afectas al IA"),
    (19, "(19) Ingresos no constitutivos de renta"),
    (20, "(20) Retiros, remesas o dividendos percibidos de otras sociedades"),
    (21, "(21) Crédito por IDPC correspondiente a retiros percibidos"),
    (22, "(22) Restitución del crédito por IDPC correspondiente a retiros percibidos"),
    (23, "(23) Retiros percibidos de otras sociedades afectos a IGC o IA"),
    (24, "(24) Retiros percibidos de otras sociedades exentos de IGC"),
    (25, "(25) Retiros percibidos de otras sociedades como INR"),
    (26, "(26) Crédito por impuesto territorial"),
    (27, "(27) Crédito total por impuestos pagados en el exterior (STUT)"),
    (28, "(28) Crédito por impuestos pagados en el exterior, con derecho a devolución"),
    (29, "(29) Crédito por impuestos pagados en el exterior, sin derecho a devolución"),
    (30, "(30) Crédito por IDPC sobre rentas atribuidas de entidades extranjeras"),
    (31, "(31) Crédito por impuestos pagados en el exterior sobre rentas atribuidas"),
    (32, "(32) Crédito por impuestos pagados en el exterior (atribuidas), con devolución"),
    (33, "(33) Crédito por impuestos pagados en el exterior (atribuidas), sin devolución"),
    (34, "(34) Exceso de crédito por IDPC no sujeto a restitución"),
    (35, "(35) Exceso de crédito por IDPC sujeto a restitución"),
    (36, "(36) Exceso de crédito por impuestos pagados en el exterior"),
    (37, "(37) Dividendo o distribución absorbida por pérdidas tributarias"),
]

class Command(BaseCommand):
    help = 'Puebla la tabla ConceptoFactor con los datos oficiales de la DJ 1949.'

    @transaction.atomic
    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.SUCCESS('Iniciando la carga de conceptos para la DJ 1949...'))
        
        conceptos_creados = 0
        for columna, descripcion in FACTORES_DJ1949:
            _, created = ConceptoFactor.objects.update_or_create(
                columna_dj=columna,
                defaults={'descripcion': descripcion}
            )
            if created:
                conceptos_creados += 1
        
        self.stdout.write(self.style.SUCCESS(f'¡Proceso completado! Se crearon {conceptos_creados} nuevos conceptos.'))
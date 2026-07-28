"""
Carga leads DEMO ficticios en la base (para desarrollo).

Son los mismos 9 registros del SEED del mock, así al conectar el frontend al
backend se ve la MISMA data pero ahora desde MySQL. Cero PII.

    python manage.py seed_demo            # agrega los demos
    python manage.py seed_demo --flush    # borra todo y recarga
"""
from datetime import date, datetime, time

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from crm.models import Lead, LeadHistorial

# (fecha, cliente, servicio, mail, telefono, origen, sub_origen, resp, estado, sub_estado, comentario)
DEMO = [
    ("2026-06-18", "Acme Logística SA", "Almacenamiento", "contacto@acme-demo.example", "1155550001", "Google Ads", "Landing page", "Camila", "1. Datos pendientes", "", ""),
    ("2026-06-02", "Distribuidora Ejemplo SRL", "Cross-docking", "ventas@distri-ejemplo.example", "1155550002", "Meta Ads", "Formulario web", "Cesar", "2. Pendiente cotizar", "", "Pidió cotización por 200 pallets."),
    ("2026-05-20", "Importadora Ficticia SA", "Almacenamiento", "compras@import-ficticia.example", "1155550003", "Referido", "Cliente actual", "Camila", "3. Cotizado", "", "Cotización enviada 20/05."),
    ("2026-05-05", "Textiles Prueba SRL", "Almacenamiento", "info@textiles-prueba.example", "1155550004", "Redes sociales", "", "Cesar", "4. Interesado", "", "Quiere visita al depósito."),
    ("2026-04-10", "Alimentos Demo SA", "Cross-docking", "logistica@alimentos-demo.example", "1155550005", "SIGNOS", "Landing page", "Camila", "5. Negociando / Re-cotizar", "", "Negociando precio por volumen."),
    ("2026-03-22", "Norte Mayorista SRL", "Almacenamiento", "gerencia@norte-mayorista.example", "1155550006", "Referido", "Proveedor", "Cesar", "6. Venta ganada", "", "Contrato firmado."),
    ("2026-03-08", "Química Muestra SA", "Almacenamiento", "contacto@quimica-muestra.example", "1155550007", "Sitio web", "", "Camila", "7. No viable", "SENASA", "Requiere habilitación que no tenemos."),
    ("2026-02-14", "Comercial Testeo SRL", "Cross-docking", "ventas@comercial-testeo.example", "1155550008", "Meta Ads", "Formulario web", "Cesar", "8. No avanzó", "Sin respuesta", "Dejó de responder."),
    ("2026-02-01", "Servicios Ejemplo SA", "Almacenamiento", "info@servicios-ejemplo.example", "1155550009", "Google Ads", "Landing page", "Camila", "3. Cotizado", "", "Sin novedades hace tiempo."),
]


class Command(BaseCommand):
    help = "Carga leads demo ficticios (dev)."

    def add_arguments(self, parser):
        parser.add_argument("--flush", action="store_true",
                            help="Borra leads y tally antes de cargar.")

    @transaction.atomic
    def handle(self, *args, **opts):
        User = get_user_model()
        if opts["flush"]:
            LeadHistorial.objects.all().delete()
            Lead.objects.all().delete()

        users = {}

        def get_user(nombre):
            if nombre not in users:
                users[nombre], _ = User.objects.get_or_create(
                    username=nombre.lower(),
                    defaults={"first_name": nombre, "is_staff": True},
                )
            return users[nombre]

        n = 0
        for (fecha, cliente, servicio, mail, tel, origen, sub_origen,
             resp, estado, sub_estado, comentario) in DEMO:
            f = date.fromisoformat(fecha)
            lead = Lead.objects.create(
                fecha=f, cliente=cliente, servicio=servicio, mail=mail,
                telefono=tel, origen=origen, sub_origen=sub_origen,
                responsable=get_user(resp), estado=estado,
                sub_estado=sub_estado, estado_fecha=f,
            )
            if comentario:
                ts = timezone.make_aware(datetime.combine(f, time(9, 0)))
                LeadHistorial.objects.create(
                    lead=lead, ts=ts, texto=comentario, autor=get_user(resp)
                )
            n += 1

        self.stdout.write(self.style.SUCCESS(f"{n} leads demo cargados."))

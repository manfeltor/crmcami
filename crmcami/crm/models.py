from datetime import date

from django.conf import settings
from django.db import models

from . import choices


class Lead(models.Model):
    fecha = models.DateField("Fecha de ingreso", null=True, blank=True)
    cliente = models.CharField(max_length=255)
    servicio = models.CharField(
        max_length=40, choices=choices.SERVICIO_CHOICES, blank=True
    )
    mail = models.EmailField(blank=True)
    telefono = models.CharField(max_length=50, blank=True)  # texto: hay +54, 0, etc.
    origen = models.CharField(
        max_length=40, choices=choices.ORIGEN_CHOICES, blank=True
    )
    sub_origen = models.CharField(max_length=255, blank=True)

    # 'resp' del mock (texto) -> FK al User. Se auto-asigna al usuario logueado
    # y evita "Cami R"/"Camila" inconsistentes.
    responsable = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="leads",
    )

    estado = models.CharField(
        max_length=40,
        choices=choices.ESTADO_CHOICES,
        default=choices.ESTADO_DATOS_PENDIENTES,
    )
    sub_estado = models.CharField(
        max_length=60, choices=choices.SUB_ESTADO_CHOICES, blank=True
    )
    estado_fecha = models.DateField(
        "Fecha del ultimo cambio de estado", null=True, blank=True
    )

    # Idempotencia del pull de WordPress (Paso 5): id de la entry en Formidable.
    # unico -> evita duplicados y protege de dos syncs simultaneos. null en los
    # leads cargados a mano; MySQL permite varios NULL en un indice unico.
    wp_entry_id = models.CharField(
        max_length=100, null=True, blank=True, unique=True
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-fecha", "-created_at"]

    def __str__(self):
        return self.cliente

    # --- comentarios: DERIVADO del historial (NO es una columna) ------------
    @property
    def comentarios(self):
        """
        String con todo el historial pegoteado, tal como lo usa el mock para
        buscar / tooltip / export. Se calcula al vuelo desde LeadHistorial:
        una sola fuente de verdad, nunca se desincroniza.
        (Al servirlo por API, prefetch_related('historial') evita el N+1.)
        """
        return "\n".join(
            f"{h.ts:%d/%m/%Y %H:%M} - {h.texto}" for h in self.historial.all()
        )

    # --- logica de "alerta +30 dias" (portada de isStale del mock) ----------
    @property
    def ultima_actividad(self):
        best = self.estado_fecha or self.fecha
        for h in self.historial.all():
            d = h.ts.date()
            if best is None or d > best:
                best = d
        return best

    @property
    def es_final(self):
        return self.estado in choices.ESTADOS_FINALES

    def dias_inactivo(self, hoy=None):
        ref = self.ultima_actividad
        if ref is None:
            return None
        return ((hoy or date.today()) - ref).days

    def is_stale(self, hoy=None):
        if self.es_final:
            return False
        d = self.dias_inactivo(hoy)
        return d is not None and d > choices.DIAS_ALERTA_STALE


class LeadHistorial(models.Model):
    """
    Un movimiento del lead: comentario/avance o cambio de estado, con fecha y
    hora. Reemplaza el array 'historial[]' que en el mock vivia adentro del lead.
    """

    lead = models.ForeignKey(
        Lead, on_delete=models.CASCADE, related_name="historial"
    )
    ts = models.DateTimeField("Fecha y hora")
    texto = models.TextField()
    autor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )

    class Meta:
        ordering = ["-ts"]

    def __str__(self):
        return f"{self.ts:%d/%m/%Y %H:%M} - {self.texto[:40]}"


class TallyNoComercial(models.Model):
    """Contador de contactos no comerciales por fecha y categoria (el 'tally')."""

    fecha = models.DateField()
    categoria = models.CharField(max_length=40, choices=choices.NOCOM_CHOICES)
    cantidad = models.PositiveIntegerField(default=0)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["fecha", "categoria"], name="uniq_tally_fecha_categoria"
            )
        ]
        ordering = ["-fecha"]

    def __str__(self):
        return f"{self.fecha} · {self.categoria}: {self.cantidad}"

from django.db import models


class SyncState(models.Model):
    """
    Estado del sync con WordPress (registro unico / singleton).

    `watermark` = el mayor id de submission (frm_items) ya procesado. El sync
    solo mira submissions con id > watermark y avanza la marca. Al ser
    forward-only, un lead borrado en el CRM NO se vuelve a importar (su
    submission ya quedo atras de la marca).
    """

    watermark = models.BigIntegerField(default=0)
    last_sync_at = models.DateTimeField(null=True, blank=True)
    last_ok = models.BooleanField(default=True)
    last_error = models.TextField(blank=True, default="")
    last_importados = models.IntegerField(default=0)

    class Meta:
        verbose_name = "Estado de sincronizacion WP"
        verbose_name_plural = "Estado de sincronizacion WP"

    def __str__(self):
        return f"SyncState(wm={self.watermark}, last={self.last_sync_at})"

    @classmethod
    def solo(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

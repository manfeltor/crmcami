from django.contrib import admin

from .models import SyncState


@admin.register(SyncState)
class SyncStateAdmin(admin.ModelAdmin):
    list_display = ("watermark", "last_sync_at", "last_ok", "last_importados")
    readonly_fields = (
        "watermark", "last_sync_at", "last_ok", "last_error", "last_importados",
    )

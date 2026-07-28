from django.contrib import admin

from .models import Lead, LeadHistorial, TallyNoComercial


class LeadHistorialInline(admin.TabularInline):
    model = LeadHistorial
    extra = 0
    fields = ("ts", "texto", "autor")


@admin.register(Lead)
class LeadAdmin(admin.ModelAdmin):
    list_display = (
        "cliente",
        "servicio",
        "estado",
        "origen",
        "responsable",
        "fecha",
        "estado_fecha",
    )
    list_filter = ("estado", "servicio", "origen", "responsable")
    search_fields = ("cliente", "mail", "telefono", "sub_origen")
    date_hierarchy = "fecha"
    inlines = [LeadHistorialInline]
    readonly_fields = ("wp_entry_id", "created_at", "updated_at")


@admin.register(TallyNoComercial)
class TallyNoComercialAdmin(admin.ModelAdmin):
    list_display = ("fecha", "categoria", "cantidad")
    list_filter = ("categoria",)
    date_hierarchy = "fecha"

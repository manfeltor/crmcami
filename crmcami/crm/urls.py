from django.urls import path

from . import api

urlpatterns = [
    path("leads/", api.leads, name="api_leads"),                          # GET lista · POST crea
    path("leads/bulk-estado/", api.bulk_estado, name="api_bulk_estado"),  # POST cambio masivo
    path("leads/bulk-delete/", api.bulk_delete, name="api_bulk_delete"),  # POST borrado masivo
    path("leads/<int:pk>/", api.lead_detail, name="api_lead_detail"),     # POST edita
    path("leads/import/", api.leads_import, name="api_leads_import"),     # POST reemplaza todo
    path("tally/", api.tally, name="api_tally"),                          # GET lista · POST +/-
]

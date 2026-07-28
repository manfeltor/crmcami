from django.urls import path

from . import api

urlpatterns = [
    path("leads/", api.leads, name="api_leads"),               # GET lista · POST crea
    path("leads/<int:pk>/", api.lead_detail, name="api_lead_detail"),  # POST edita
]

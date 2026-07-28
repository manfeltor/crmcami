from django.urls import path

from . import api

urlpatterns = [
    path("leads/", api.leads_json, name="api_leads"),
]

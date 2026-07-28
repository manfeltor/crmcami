from django.urls import path

from . import views

urlpatterns = [
    path("sync/", views.sync_now, name="wp_sync"),   # POST {force?} -> pull WP
]

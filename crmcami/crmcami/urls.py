"""
URL configuration for crmcami project.
https://docs.djangoproject.com/en/6.0/topics/http/urls/
"""
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import path

from . import views

urlpatterns = [
    path("admin/", admin.site.urls),

    # --- Autenticacion (session auth nativa de Django) ---
    path("login/", auth_views.LoginView.as_view(), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),

    # --- Home = el SPA ---
    # Sirve crm_mock.html crudo, detras de login_required (ver views.spa).
    path("", views.spa, name="home"),
]

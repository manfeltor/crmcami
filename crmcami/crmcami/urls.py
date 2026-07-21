"""
URL configuration for crmcami project.
https://docs.djangoproject.com/en/6.0/topics/http/urls/
"""
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import login_required
from django.urls import path
from django.views.generic import TemplateView

urlpatterns = [
    path("admin/", admin.site.urls),

    # --- Autenticacion (session auth nativa de Django) ---
    # LoginView usa el template templates/registration/login.html por defecto.
    path("login/", auth_views.LoginView.as_view(), name="login"),
    # LogoutView en Django 5+/6 SOLO acepta POST (por seguridad).
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),

    # --- Home protegida ---
    # Placeholder: cualquiera que no este logueado es redirigido a /login/.
    # Aca despues servimos el SPA (crm_mock.html).
    path(
        "",
        login_required(TemplateView.as_view(template_name="home.html")),
        name="home",
    ),
]

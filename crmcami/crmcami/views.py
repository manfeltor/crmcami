"""Vistas del proyecto crmcami."""
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import FileResponse
from django.views.decorators.csrf import ensure_csrf_cookie

# El SPA (frontend) es un unico archivo autonomo (crm_mock.html). Se sirve CRUDO:
# NO pasa por el template engine de Django, porque el JSX usa {{ }} (estilos
# inline de React) que Django malinterpretaria como variables de template.
SPA_FILE = settings.BASE_DIR / "frontend" / "crm_mock.html"


@login_required
@ensure_csrf_cookie  # deja la cookie 'csrftoken' para que el JS la mande en los POST
def spa(request):
    """
    Sirve el CRM (crm_mock.html) detras del login.

    Cero datos por ahora: el HTML trae su propia data ficticia (SEED). Los datos
    reales van a llegar cuando cada metodo del DataAPI (dentro del HTML) pase de
    'return hardcodeado' a 'fetch()' contra los endpoints de Django.
    """
    return FileResponse(open(SPA_FILE, "rb"), content_type="text/html")

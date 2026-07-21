from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User

# Registramos nuestro User en el /admin usando UserAdmin, que es la pantalla
# de administracion de usuarios que ya trae Django (crear usuario, cambiar
# password de forma segura, marcar is_staff/is_superuser, asignar grupos...).
# Sin esto, el User no apareceria en el admin.
admin.site.register(User, UserAdmin)

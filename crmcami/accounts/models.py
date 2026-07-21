from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    """
    Usuario del CRM.

    Hereda de AbstractUser => ya trae TODO lo del usuario nativo de Django:
      - username, password (hasheada), email, first_name, last_name
      - is_active   -> si puede loguearse
      - is_staff    -> si puede entrar al /admin
      - is_superuser-> tiene todos los permisos
      - groups / user_permissions -> sistema de permisos (opt-in en tu API)
      - last_login, date_joined

    Por ahora esta VACIO (no agrega campos): se comporta igual que el User
    built-in. Existe desde el dia 0 a proposito, porque cambiar el modelo de
    usuario DESPUES del primer migrate es una migracion dolorosa. Teniendolo
    ya, el dia que necesites sumar un campo (telefono, rol, avatar, etc.) es
    tan simple como agregarlo aca abajo y correr una migracion.
    """

    # Ejemplo de a futuro (hoy comentado, no agrega nada):
    # telefono = models.CharField(max_length=30, blank=True)

    pass

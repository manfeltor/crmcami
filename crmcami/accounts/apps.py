from django.apps import AppConfig


class AccountsConfig(AppConfig):
    # tipo de PK por defecto para los modelos de esta app
    default_auto_field = "django.db.models.BigAutoField"
    # nombre/etiqueta de la app -> el "accounts" de AUTH_USER_MODEL = "accounts.User"
    name = "accounts"

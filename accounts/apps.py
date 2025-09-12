# accounts/apps.py
from django.apps import AppConfig


class AccountsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'accounts'
    verbose_name = 'Gestión de Cuentas de Usuario'

    def ready(self):
        # Importar señales si las tienes
        # import accounts.signals
        pass
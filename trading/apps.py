from django.apps import AppConfig


class TradingConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'trading'
    verbose_name = 'Trading'

    def ready(self):
        import trading.signals
        import messaging.signals

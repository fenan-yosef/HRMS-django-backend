from django.apps import AppConfig


class TasksConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'tasks'

    def ready(self):
        # Import signals on app ready
        try:
            import tasks.signals  # noqa: F401
        except Exception:
            # Avoid crashing on initial migrate before tables exist
            pass

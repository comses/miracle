from django.apps import AppConfig

class MiracleCoreConfig(AppConfig):
    name = 'miracle.core'
    verbose_name = 'Miracle core services'

    def ready(self):
        from .signals import create_project_group

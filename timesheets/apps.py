from django.apps import AppConfig


class TimesheetsConfig(AppConfig):
    name = 'timesheets'
    verbose_name = "Timesheets Galore"

    def ready(self):
        import timesheets.signals

from django.contrib import admin

from . import models

for model_class in (models.Project, models.Dataset, models.MiracleUser, models.Author, models.DataAnalysisScript,
                    models.DataTable, models.DataTableColumn, models.ActivityLog):
    admin.site.register(model_class)

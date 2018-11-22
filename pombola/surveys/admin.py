from django.contrib import admin

from sorl.thumbnail.admin import AdminImageMixin

from pombola.surveys.models import Survey


class SurveyAdmin(AdminImageMixin, admin.ModelAdmin):
  pass
admin.site.register(Survey, SurveyAdmin)

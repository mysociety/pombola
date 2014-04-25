from django.contrib import admin
from django.forms import ModelForm, ValidationError

from . import models


class ExperimentAdmin(admin.ModelAdmin):
    search_fields = [ 'name' ]
    list_display  = [ 'name', 'slug' ]

    prepopulated_fields = {'slug': ['name']}


class EventAdmin(admin.ModelAdmin):
    form = EventAdminForm
    list_display = ['experiment', 'user_key', 'variant', 'category',
                    'action', 'label', 'extra_data']
    ordering = ('-created',)


admin.site.register(models.Experiment, ExperimentAdmin)
admin.site.register(models.Event, EventAdmin)

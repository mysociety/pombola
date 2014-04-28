import json

from django.contrib import admin
from django.forms import ModelForm, ValidationError

from . import models


class ExperimentAdmin(admin.ModelAdmin):
    search_fields = [ 'name' ]
    list_display  = [ 'name', 'slug' ]

    prepopulated_fields = {'slug': ['name']}


class EventAdminForm(ModelForm):
    def clean_extra_data(self):
        extra_data = self.cleaned_data['extra_data']
        if extra_data.strip():
            try:
                json.loads(extra_data)
            except ValueError, ve:
                message = "The extra data must be empty or valid JSON: {0}"
                raise ValidationError, message.format(ve)
        return extra_data


class EventAdmin(admin.ModelAdmin):
    form = EventAdminForm
    list_display = ['experiment', 'user_key', 'variant', 'category',
                    'action', 'label', 'extra_data']
    ordering = ('-created',)


admin.site.register(models.Experiment, ExperimentAdmin)
admin.site.register(models.Event, EventAdmin)

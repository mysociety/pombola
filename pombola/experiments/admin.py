import csv
import json
from StringIO import StringIO

from django.contrib import admin, messages
from django.forms import ModelForm, ValidationError
from django.http import HttpResponse

from . import models


class ExperimentAdmin(admin.ModelAdmin):
    search_fields = [ 'name' ]
    list_display  = [ 'name', 'slug' ]

    prepopulated_fields = {'slug': ['name']}

    actions = ['export_csv']

    def export_csv(self, request, queryset):
        """This admin action returns a CSV file of all events in an experiment"""
        if queryset.count() != 1:
            self.message_user(request,
                              "You can only export 1 experiment as CSV",
                              level=messages.ERROR)
            return
        experiment = queryset[0]
        basic_fields = [
            'id', 'user_key', 'variant', 'category', 'action', 'label',
            'created'
        ]
        # We also add a column for each distinct key which is used in
        # extra_data:
        extra_fields = sorted(experiment.extra_fields)
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(basic_fields + extra_fields)
        for event in experiment.event_set.all():
            row = [getattr(event, key) for key in basic_fields]
            extra_data = json.loads(event.extra_data)
            row += [extra_data.get(key, '') for key in extra_fields]
            writer.writerow(row)
        response = HttpResponse(output.getvalue(), content_type='text/csv')
        disposition = 'attachment; filename={0}.csv'.format(experiment.slug)
        response['Content-Disposition'] = disposition
        return response

    export_csv.short_description = "Export an experiment's data as CSV"


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

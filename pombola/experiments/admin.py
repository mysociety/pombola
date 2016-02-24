import csv
from collections import defaultdict
import json
import re
from StringIO import StringIO

from django.contrib import admin, messages
from django.forms import ModelForm, ValidationError
from django.http import HttpResponse

from pombola.feedback.models import Feedback

from . import models

def get_youth_employment_feedback_comments_by_users():
    '''Extract Feedback which is storing comments on the Youth Employment page

    Unfortunately when we ran the earlier experiments it was suggested that we
    store free text comments as Feedback objects since they would be handled
    manually like other user feedback. Now, however, it's a requirement to add
    the comments to the CSV export of experiment data. To deal with this after
    the fact, this extracts all comments stored in Feedback and returns them
    in a dictionary with a list of comments for each user_key.'''
    result = defaultdict(list)
    for feedback in Feedback.objects.filter(
            status='non-actionable',
            comment__contains='user_key',
            url__endswith='youth-employment/comment',
    ).order_by('created'):
        m = re.match(r'(?ms)^(?P<json>\{.*?\}) (?P<comment>.*)$', feedback.comment)
        if not m:
            continue
        data = json.loads(m.group('json'))
        comment = m.group('comment')
        result[data['user_key']].append(comment)
    return result

def is_youth_employment_comment_event(event):
    return (
        event.category == 'form' and
        event.action == 'submit' and
        event.label == 'comment'
    )

@admin.register(models.Experiment)
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
        comments_by_user = get_youth_employment_feedback_comments_by_users()
        # We also add a column for each distinct key which is used in
        # extra_data:
        extra_fields = sorted(experiment.extra_fields)
        # An extra column for comments that had to be extracted from
        # the feedback table:
        extra_fields.append('feedback_comment')
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(basic_fields + extra_fields)
        for event in experiment.event_set.order_by('created'):
            row = [getattr(event, key) for key in basic_fields]
            extra_data = json.loads(event.extra_data)
            # An unpleasant special case to include comments that were
            # submitted which are stored in a different table not
            # linked by a foreign key, sigh.
            if experiment.slug == 'youth-employment-bill':
                if is_youth_employment_comment_event(event):
                    user_comments = comments_by_user[event.user_key]
                    extra_data['feedback_comment'] = \
                        user_comments.pop(0).encode('utf-8')
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


@admin.register(models.Event)
class EventAdmin(admin.ModelAdmin):
    form = EventAdminForm
    list_display = ['experiment', 'user_key', 'variant', 'category',
                    'action', 'label', 'extra_data']
    ordering = ('-created',)

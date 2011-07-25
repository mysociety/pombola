from django.contrib import admin
import models
from django.contrib.gis import db
from django.core.urlresolvers import reverse
from django.contrib.contenttypes.generic import GenericTabularInline
from django import forms

# from django.contrib.gis import db
# from django.core.urlresolvers import reverse
from django.contrib.contenttypes.generic import GenericTabularInline
# from django import forms

def create_admin_link_for(obj, link_text):
    url = reverse(
        'admin:%s_%s_change' % ( obj._meta.app_label, obj._meta.module_name),
        args=[obj.id]
    )
    return u'<a href="%s">%s</a>' % ( url, link_text )


class TaskAdmin(admin.ModelAdmin):
    list_display  = [ 'task_code', 'show_foreign', 'defer_until', ]
    list_filter   = [ 'task_code', ]
    # search_fields = [ 'task_code', ]

    def show_foreign(self, obj):
        return create_admin_link_for( obj.content_object, str(obj.content_object) )
    show_foreign.allow_tags = True


# class TaskInlineAdmin(GenericTabularInline):
#     model      = models.Task
#     extra      = 0
#     can_delete = False
#     fields     = [ 'task_code' ]


# Add these to the admin
admin.site.register( models.Task, TaskAdmin )

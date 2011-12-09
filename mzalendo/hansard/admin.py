from django.contrib import admin
import models

from ajax_select import make_ajax_form
from ajax_select.admin import AjaxSelectAdmin

# from django.contrib.gis import db
# from django.core.urlresolvers import reverse
# from django.contrib.contenttypes.generic import GenericTabularInline
# from django import forms
# 
# def create_admin_link_for(obj, link_text):
#     return u'<a href="%s">%s</a>' % ( obj.get_admin_url(), link_text )


class SourceAdmin(admin.ModelAdmin):
    list_display  = [ 'name', 'date', 'last_processing_success', 'last_processing_attempt' ]
    list_filter = ('date', 'last_processing_success')
    date_hierarchy = 'date'
    

class VenueAdmin(admin.ModelAdmin):
    list_display  = [ 'slug', 'name' ]


class SittingAdmin(admin.ModelAdmin):
    list_display  = [ 'start_date', 'start_time', 'end_date', 'end_time', 'source' ]
    list_filter = ['start_date']
    date_hierarchy = 'start_date'
    

class EntryAdmin(admin.ModelAdmin):
    list_display  = [ 'sitting', 'type', 'speaker_name', '__unicode__' ]
    

class AliasAdmin(admin.ModelAdmin):
    form = make_ajax_form(
        models.Alias,
        {
            'person':       'person_name',
        }
    )    


admin.site.register( models.Source,  SourceAdmin )
admin.site.register( models.Venue,   VenueAdmin )
admin.site.register( models.Sitting, SittingAdmin )
admin.site.register( models.Entry,   EntryAdmin )
admin.site.register( models.Alias,   AliasAdmin )

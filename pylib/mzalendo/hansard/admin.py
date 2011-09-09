from django.contrib import admin
import models

# from django.contrib.gis import db
# from django.core.urlresolvers import reverse
# from django.contrib.contenttypes.generic import GenericTabularInline
# from django import forms
# 
# def create_admin_link_for(obj, link_text):
#     return u'<a href="%s">%s</a>' % ( obj.get_admin_url(), link_text )


class ChunkAdmin(admin.ModelAdmin):
    pass
    list_display  = [ 'date', 'session', 'type', '__unicode__' ]
    

admin.site.register( models.Chunk, ChunkAdmin )

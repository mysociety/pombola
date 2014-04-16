import os

from django.contrib import admin
from django.utils.text import slugify

from pombola.file_archive import models

class FileAdmin(admin.ModelAdmin):
    list_display  = [ 'slug', 'updated' ]
    search_fields = [ 'slug' ]

    fields = [ 'file' ]

admin.site.register( models.File, FileAdmin )

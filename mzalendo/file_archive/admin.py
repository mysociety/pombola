from django.contrib import admin
from file_archive import models

class FileAdmin(admin.ModelAdmin):
    list_display  = [ 'slug', 'updated' ]
    search_fields = [ 'slug' ]

admin.site.register( models.File, FileAdmin )

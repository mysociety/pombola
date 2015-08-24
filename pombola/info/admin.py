from django.conf import settings
from django.contrib import admin

import autocomplete_light

import models

from pombola.slug_helpers.admin import StricterSlugFieldMixin

class LabelAdmin(admin.ModelAdmin):
    search_fields = [ 'name' ]
    list_display  = [ 'name', 'slug' ]

    prepopulated_fields = {'slug': ['name']}

if settings.INFO_PAGES_ALLOW_RAW_HTML:
    search_fields_to_use = ['title', 'markdown_content', 'raw_content']
    fields_to_use = (
        'title', 'slug', 'publication_date', 'kind', 'use_raw',
        'markdown_content', 'raw_content', 'categories', 'tags',
        'featured_image_file',
    )
else:
    search_fields_to_use = ['title', 'markdown_content']
    fields_to_use = (
        'title', 'slug', 'publication_date', 'kind',
        'markdown_content', 'categories', 'tags',
        'featured_image_file',
    )

class InfoPageAdmin(StricterSlugFieldMixin, admin.ModelAdmin):
    search_fields = search_fields_to_use
    list_display  = [ 'slug', 'title', 'kind', 'publication_date' ]
    list_filter   = [ 'kind', 'categories', 'tags' ]
    date_hierarchy = 'publication_date'
    ordering = ('-publication_date', 'title')

    form = autocomplete_light.modelform_factory(models.InfoPage)

    fields = fields_to_use
    prepopulated_fields = {'slug': ['title']}

    class Media:
        js = ("info/js/admin.js",)


admin.site.register( models.Category, LabelAdmin )
admin.site.register( models.Tag,      LabelAdmin )
admin.site.register( models.InfoPage, InfoPageAdmin )

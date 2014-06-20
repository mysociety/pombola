from django.contrib import admin

import autocomplete_light

import models

from pombola.slug_helpers.admin import StricterSlugFieldMixin

class LabelAdmin(admin.ModelAdmin):
    search_fields = [ 'name' ]
    list_display  = [ 'name', 'slug' ]

    prepopulated_fields = {'slug': ['name']}


class InfoPageAdmin(StricterSlugFieldMixin, admin.ModelAdmin):
    search_fields = [ 'title', 'content' ]
    list_display  = [ 'slug', 'title', 'kind', 'publication_date' ]
    list_filter   = [ 'kind', 'categories', 'tags' ]
    date_hierarchy = 'publication_date'
    ordering = ('-publication_date', 'title')

    form = autocomplete_light.modelform_factory(models.InfoPage)

    fields = ('title', 'slug', 'publication_date', 'kind', 'content', 'categories', 'tags')
    prepopulated_fields = {'slug': ['title']}


admin.site.register( models.Category, LabelAdmin )
admin.site.register( models.Tag,      LabelAdmin )
admin.site.register( models.InfoPage, InfoPageAdmin )

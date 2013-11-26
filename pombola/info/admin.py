from django.contrib import admin
import models

class LabelAdmin(admin.ModelAdmin):
    search_fields = [ 'name' ]
    list_display  = [ 'name', 'slug' ]

    fields = ('name', 'slug')
    prepopulated_fields = {'slug': ['name']}

class InfoPageAdmin(admin.ModelAdmin):
    search_fields = [ 'title', 'content' ]
    list_display  = [ 'slug', 'title', 'kind' ]
    list_filter   = [ 'kind', 'categories', 'tags' ]

    fields = ('title', 'slug', 'publication_date', 'kind', 'content', 'categories', 'tags')
    prepopulated_fields = {'slug': ['title']}


admin.site.register( models.Category, LabelAdmin )
admin.site.register( models.Tag,      LabelAdmin )
admin.site.register( models.InfoPage, InfoPageAdmin )

from django.contrib import admin
import models

class InfoPageAdmin(admin.ModelAdmin):
    search_fields = [ 'title', 'content' ]
    list_display  = [ 'slug', 'title', 'kind' ]
    list_filter   = [ 'kind' ]

    fields = ('title', 'slug', 'publication_date', 'kind', 'content')
    prepopulated_fields = {'slug': ['title']}


admin.site.register( models.InfoPage, InfoPageAdmin )

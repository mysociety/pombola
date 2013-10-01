from django.contrib import admin
import models

class CategoryAdmin(admin.ModelAdmin):
    search_fields = [ 'name' ]
    list_display  = [ 'name', 'slug' ]

    fields = ('name', 'slug')
    prepopulated_fields = {'slug': ['name']}

class InfoPageAdmin(admin.ModelAdmin):
    search_fields = [ 'title', 'content' ]
    list_display  = [ 'slug', 'title', 'kind' ]
    list_filter   = [ 'kind', 'categories' ]

    fields = ('title', 'slug', 'publication_date', 'kind', 'content', 'categories')
    prepopulated_fields = {'slug': ['title']}


admin.site.register( models.Category, CategoryAdmin )
admin.site.register( models.InfoPage, InfoPageAdmin )

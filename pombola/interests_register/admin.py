from django.contrib import admin

from . import models


class CategoryAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug": ["name"]}
    list_display = ['slug', 'name', 'sort_order']
    search_fields = ['name']


class ReleaseAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug": ["name"]}
    list_display = ['slug', 'name', 'date']
    search_fields = ['name']
    date_hierarchy = 'date'


class LineItemInlineAdmin(admin.TabularInline):
    model = models.EntryLineItem
    # extra = 2
    fields = [ 'key', 'value' ]


class EntryAdmin(admin.ModelAdmin):
    inlines = [LineItemInlineAdmin]
    list_display = ['id', 'person', 'category', 'release', 'sort_order']
    list_filter = [ 'release', 'category' ]
    search_fields = ['person__legal_name']


# Add these to the admin
admin.site.register( models.Category, CategoryAdmin)
admin.site.register( models.Release, ReleaseAdmin)
admin.site.register( models.Entry, EntryAdmin)

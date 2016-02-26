from django.contrib import admin

from . import models

from pombola.slug_helpers.admin import StricterSlugFieldMixin


@admin.register(models.Category)
class CategoryAdmin(StricterSlugFieldMixin, admin.ModelAdmin):
    prepopulated_fields = {"slug": ["name"]}
    list_display = ['slug', 'name', 'sort_order']
    search_fields = ['name']


@admin.register(models.Release)
class ReleaseAdmin(StricterSlugFieldMixin, admin.ModelAdmin):
    prepopulated_fields = {"slug": ["name"]}
    list_display = ['slug', 'name', 'date']
    search_fields = ['name']
    date_hierarchy = 'date'


class LineItemInlineAdmin(admin.TabularInline):
    model = models.EntryLineItem
    # extra = 2
    fields = [ 'key', 'value' ]


@admin.register(models.Entry)
class EntryAdmin(admin.ModelAdmin):
    inlines = [LineItemInlineAdmin]
    list_display = ['id', 'person', 'category', 'release', 'sort_order']
    list_filter = [ 'release', 'category' ]
    search_fields = ['person__legal_name']

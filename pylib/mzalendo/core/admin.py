from django.contrib import admin
from mzalendo.core import models

class PositionAdmin(admin.ModelAdmin):
    pass

class PositionInlineAdmin(admin.TabularInline):
    model = models.Position
    extra = 0
    can_delete = False
    fields = [ 'person', 'organisation', 'title', 'start_date', 'end_date' ]


class PersonAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug": ("first_name","last_name")}
    inlines = [ PositionInlineAdmin ]

class PlaceAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug": ("name",)}


class PlaceInlineAdmin(admin.TabularInline):
    model = models.Place
    extra = 0
    can_delete = False
    fields = [ 'name', 'slug', 'place_type' ]


class OrganisationAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug": ("name",)}
    inlines = [ PlaceInlineAdmin, PositionInlineAdmin ]


# Add these to the admin
admin.site.register( models.Person,       PersonAdmin       )
admin.site.register( models.Organisation, OrganisationAdmin )
admin.site.register( models.Place,        PlaceAdmin        )
admin.site.register( models.Position,     PositionAdmin        )

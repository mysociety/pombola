from django.contrib import admin
from mzalendo.core import models

class PersonAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug": ("first_name","last_name")}


class OrganisationAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug": ("name",)}


class PlaceAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug": ("name",)}


# Add these to the admin
admin.site.register( models.Person,       PersonAdmin       )
admin.site.register( models.Organisation, OrganisationAdmin )
admin.site.register( models.Place,        PlaceAdmin        )

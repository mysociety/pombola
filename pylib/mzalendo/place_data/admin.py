from django.contrib import admin
from place_data import models

class DataCategoryAdmin(admin.ModelAdmin):
    pass

class DataAdmin(admin.ModelAdmin):
    pass

admin.site.register( models.DataCategory, DataCategoryAdmin )
admin.site.register( models.Data,         DataAdmin )


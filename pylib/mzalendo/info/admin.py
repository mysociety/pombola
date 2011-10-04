from django.contrib import admin
import models

class InfoPageAdmin(admin.ModelAdmin):
    pass
    list_display  = [ 'slug', 'title' ]
    

admin.site.register( models.InfoPage, InfoPageAdmin )

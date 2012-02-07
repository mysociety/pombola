from django.contrib import admin
import models

class ProjectAdmin(admin.ModelAdmin):
    list_display  = [ 'cdf_index', 'constituency', 'project_name' ]
    search_fields = [ 'constituency__name', 'project_name' ]
    

admin.site.register( models.Project, ProjectAdmin )

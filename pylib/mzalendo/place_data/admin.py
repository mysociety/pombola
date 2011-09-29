from django.contrib import admin
from django.shortcuts  import render_to_response, get_object_or_404, redirect
from django.template   import RequestContext

from place_data import models

class DataCategoryAdmin(admin.ModelAdmin):
    pass

class DataAdmin(admin.ModelAdmin):

    def upload_csv(self, request): 
        return render_to_response(
            'admin/place_data/data/upload_csv.html',
            {
            
            },
            context_instance=RequestContext(
                request,
                current_app=self.admin_site.name,
            ),
            
        )

    def get_urls(self):
        from django.conf.urls.defaults import *
        urls = super(DataAdmin, self).get_urls()
        my_urls = patterns('',
            url(
                r'upload_csv',
                self.admin_site.admin_view(self.upload_csv),
                name='admin_upload_csv',
            ),
        )
        return my_urls + urls
    


admin.site.register( models.DataCategory, DataCategoryAdmin )
admin.site.register( models.Data,         DataAdmin )


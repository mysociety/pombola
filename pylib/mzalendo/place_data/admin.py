from django import forms
from django.contrib import admin
from django.shortcuts  import render_to_response, get_object_or_404, redirect
from django.template   import RequestContext

from place_data import models

class DataCategoryAdmin(admin.ModelAdmin):
    pass

class DataAdminCSVUploadForm(forms.Form):
    csv_file = forms.FileField(
        label = 'CSV file',
    )

class DataAdmin(admin.ModelAdmin):

    def upload_csv(self, request):
        
        if request.method == 'POST':
            form = DataAdminCSVUploadForm(request.POST, request.FILES)
        else:
            form = DataAdminCSVUploadForm()

        if form.is_valid():
            # note - for this to work the TemporaryFileUploadHandler upload
            # handler needs to be the default
            csv_file_path = request.FILES['csv_file'].temporary_file_path()
            csv_file = open( csv_file_path )
            results = models.Data.process_csv( csv_file )
        else:
            results = None    
            
        return render_to_response(
            'admin/place_data/data/upload_csv.html',
            {
                'form': form,
            },
            context_instance=RequestContext(
                request,
                current_app=self.admin_site.name,
            ),            
        )

    def get_urls(self):
        from django.conf.urls.defaults import patterns, url
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

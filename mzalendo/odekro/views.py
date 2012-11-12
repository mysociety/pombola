import logging
from django.http import HttpResponse
from django.core.urlresolvers import reverse
from django.shortcuts import render

from odekro import forms
import json

import importer

def data_upload(request):
    if request.POST:
        form = forms.UploadForm(request.POST, request.FILES)
        if form.is_valid():
            upload = form.save(commit=False)
            xs = [chunk.splitlines() for chunk in upload.file.chunks()]
            data = []
            for x in xs:
                if isinstance(x, list):
                    data.extend(x)
                else:
                    data.append(x)
            data = ''.join(data)
            import_mps(data)
            done = True
    else:
        form = forms.UploadForm()
        done = False

    return render(request, 'data_upload.html', 
                  dict(form=form, done=done))


def import_mps(data):
    
    data = json.loads(data)
    print '>>>>>', len(data)

    importer.import_to_db(data)
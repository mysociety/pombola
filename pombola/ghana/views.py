import logging
from django.http import HttpResponse
from django.core.urlresolvers import reverse
from django.shortcuts import render

from pombola.ghana import forms
from pombola.info.models import InfoPage
import data

def info_page_upload(request):
    if request.POST:
        form = forms.InfoPageUpload(request.POST, request.FILES)
        if form.is_valid():
            upload = form.save(commit=False)
            content = contents(upload, '\n')
            title = form.cleaned_data['title']
            slug = form.cleaned_data['name'][:-3]            
            done = data.add_info_page(slug, title, content)
    else:
        form = forms.InfoPageUpload()
        done = False
    return render(request, 'info_page_upload.html',
                  dict(form=form, done=done))

def data_upload(request):
    if request.POST:
        form = forms.UploadForm(request.POST, request.FILES)
        if form.is_valid():
            upload = form.save(commit=False)
            data.add_mps_from_json(contents(upload))
            done = True
    else:
        form = forms.UploadForm()
        done = False

    return render(request, 'data_upload.html', 
                  dict(form=form, done=done))

def contents(upload, joint=''):
    xs = [chunk.splitlines() for chunk in upload.file.chunks()]
    data = []
    for x in xs:
        if isinstance(x, list):
            data.extend(x)
        else:
            data.append(x)
    return joint.join(data)    


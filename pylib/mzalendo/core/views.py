from django.shortcuts  import render_to_response, get_object_or_404, redirect
from django.template   import RequestContext
from django.views.generic.list_detail import object_detail, object_list

from mzalendo.core import models

def home(request):
    """Homepage"""
    return render_to_response(
        'core/home.html',
        {
        },
        context_instance=RequestContext(request)
    )


def person_list(request):
    return object_list(
        request,
        queryset=models.Person.objects.all(),
    )

def place_list(request):
    return object_list(
        request,
        queryset=models.Place.objects.all(),
    )

def organisation_list(request):
    return object_list(
        request,
        queryset=models.Organisation.objects.all(),
    )

def person(request, slug):
    """"""
    return object_detail(
        request,
        queryset = models.Person.objects,
        slug     = slug,
    )


def place(request, slug):
    """"""
    return object_detail(
        request,
        queryset = models.Place.objects,
        slug     = slug,
    )


def position(request, slug):
    """"""
    
    title = get_object_or_404(
        models.PositionTitle,
        slug=slug
    )
    
    positions =  title.position_set.all().order_by('person__first_name', 'person__last_name')
    
    return object_list(
        request,
        queryset = positions,
        extra_context = { 'title': title, },
    )


def organisation(request, slug):
    """"""
    return object_detail(
        request,
        queryset = models.Organisation.objects,
        slug     = slug,
    )

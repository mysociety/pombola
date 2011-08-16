from django.shortcuts  import render_to_response, get_object_or_404, redirect
from django.template   import RequestContext
from django.views.generic.list_detail import object_detail, object_list
from django.db.models import Count

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
    
    positions =  (
        title
            .position_set
            .all()
            .currently_active()
            .order_by('person__first_name', 'person__last_name')
    )
    
    return object_list(
        request,
        queryset = positions,
        extra_context = { 'title': title, },
    )


def organisation(request, slug):
    """"""

    org = get_object_or_404(
        models.Organisation,
        slug=slug
    )

    return render_to_response(
        'core/organisation_detail.html',
        {
            'object': org,
            'positions': org.position_set.all().order_by('person__first_name','person__last_name'),
        },
        context_instance=RequestContext(request)
    )


def organisation_kind(request, slug):
    """"""

    org_kind = get_object_or_404(
        models.OrganisationKind,
        slug=slug
    )
    
    orgs = (
        org_kind
            .organisation_set
            .all()
            .annotate(num_positions = Count('position'))
            .order_by('-num_positions', 'name')
    )
    
    return object_list(
        request,
        queryset = orgs,
        extra_context = { 'kind': org_kind, },
    )

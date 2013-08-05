from django.views.generic.list_detail import object_detail, object_list
from models import InfoPage

def info_page(request, slug='index'):
    """Show the page, or 'index' if no slug"""
    return object_detail(
        request,
        queryset = InfoPage.objects,
        slug     = slug,
    )


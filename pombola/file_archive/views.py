from django.contrib.contenttypes.models import ContentType
from django.shortcuts  import render_to_response, get_object_or_404, redirect

from .models import File

from pombola.core.models import SlugRedirect

def redirect_to_file(request, slug):
    """Find the file and redirect ot it, or 404"""

    try:
        sr = SlugRedirect.objects.get(content_type=ContentType.objects.get_for_model(File),
                                      old_object_slug=slug)
        return redirect(sr.new_object.file.url)
    except SlugRedirect.DoesNotExist:
        pass

    object = get_object_or_404( File, slug=slug )
    return redirect( object.file.url )

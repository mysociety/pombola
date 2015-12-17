from django.shortcuts import get_object_or_404, redirect

from models import File


def redirect_to_file(request, slug):
    """Find the file and redirect ot it, or 404"""

    object = get_object_or_404( File, slug=slug )
    return redirect( object.file.url )

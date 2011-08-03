import os
import markdown
from warnings import warn
import re

from django.shortcuts       import render_to_response, get_object_or_404, redirect
from django.template        import RequestContext
from django.http            import Http404
from django.conf            import settings
from django.core.exceptions import ImproperlyConfigured

def default(request, wiki_page='index'):
    """Find the appropriate markdown file and display it"""

    try:
        wiki_root = settings.INFO_CONTENT_DIRECTORY
    except AttributeError:
        raise ImproperlyConfigured("Please set 'INFO_CONTENT_DIRECTORY' in your settings file to the absolute path to the folder that contains your info content files")

    # strip out bad chars in the wiki_page
    wiki_page = re.sub( r'[^a-zA-Z0-9_\-]+', '', wiki_page )

    # create the full path to the wiki filename
    wiki_filename = os.path.join( wiki_root, wiki_page + '.md' )

    # check that the file exists and can be read
    if not os.path.exists( wiki_filename ):
        raise Http404

    # read in the file and convert the contents to html
    file_contents = open(wiki_filename).read()
    html_content = markdown.markdown( file_contents )

    # try to parse out a title from the markdown
    title_regex = re.compile( r'^#\s+(.*?)$', re.M )
    match = title_regex.search( file_contents )
    if match.group(1):
        title = match.group(1)
    else:
        title = 'No title'


    return render_to_response(
        'info/default.html',
        {
            "html_content": html_content,
            "title": title,
        },
        context_instance=RequestContext(request),
    )
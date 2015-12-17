from os.path import join
from urlparse import urlsplit

from bs4 import BeautifulSoup
from markdown import markdown

from django.conf import settings


def get_first_image_file(file_archive_file_class, info_page):
    """Return the first image in the post, if it's a file_archive image

    Otherwise (i.e. if there are no images or the first image is
    not one that's been uploaded to file_archive) return None.

    This is designed to be used from a migration, where you don't have
    the real InfoPage class, so we can't use .content_as_cleaned_html
    and instead have to use markdown to render the markdown to HTML."""
    if info_page.use_raw:
        html = info_page.raw_content
    else:
        html = markdown(unicode(info_page.markdown_content))
    soup = BeautifulSoup(html)
    imgs = soup.find_all('img')
    if not imgs:
        return None
    first_image_url = imgs[0]['src']
    # If this is an image uploaded to the file_archive, we expect
    # the URL to begin with the MEDIA_URL followed by 'file_archive':
    image_path = urlsplit(first_image_url).path
    media_url_path = urlsplit(settings.MEDIA_URL).path
    expected_prefix = join(media_url_path, 'file_archive')
    if not image_path.startswith(expected_prefix):
        return None
    path_after_media_url = image_path[len(media_url_path):]
    try:
        result = file_archive_file_class.objects.get(file=path_after_media_url)
    except file_archive_file_class.DoesNotExist:
        result = None
    return result

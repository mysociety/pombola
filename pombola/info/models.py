import datetime
import lxml
from lxml.html.clean import Cleaner
import re

from django.conf import settings
from django.db import models
from django.core.urlresolvers import reverse
from django.utils.text import slugify

from markitup.fields import MarkupField

from file_archive.models import File

class ModelBase(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class LabelModelBase(ModelBase):

    """
    The tags and categories are essentially the same thing in the database. Use
    a common model for most of the fields etc.
    """

    name = models.CharField(max_length=300, unique=True)
    slug = models.SlugField(unique=True)

    def __unicode__(self):
        return self.name

    class Meta():
        abstract = True
        ordering = ( 'name', )


class Category(LabelModelBase):

    summary = MarkupField(blank=True)

    class Meta():
        verbose_name_plural = 'categories'


class Tag(LabelModelBase):
    pass


class InfoPage(ModelBase):
    """
    InfoPage - store static pages in the database so they can be edited in the
    admin. Also simple blog posts.

    There are several pages on a site that are static - ie they don't change
    very often. However sometimes they need to change and it is conveniant to do
    this via the admin, rather than editing the html on disk.

    This module allows you to do that.

    Each page has a slug - which is used to identify it in the url. So for
    example if you had a site FAQ the slug might be 'faq' and its url would
    become something like http://example.com/info/faq - where 'info' is where
    these pages are stored.

    Pages also have titles - which are shown at the top of the page.

    Both slugs and titles must be unique to each page.

    The content of the page is formatted using 'markdown' - which allows you to
    include bulleted lists, headings, styling and links.

    The page with the slug 'index' is special - it is used as the index page to
    all the other info pages, and so should probably be a table of contents or
    similar.

    Pages can also be marked as 'blog' in which case they are presented in
    newest first order on the '/blog' page, and on their own blog page.
    """

    title   = models.CharField(max_length=300, unique=True)
    slug    = models.SlugField(unique=True)
    markdown_content = MarkupField(
        blank=True,
        default='',
        help_text="When linking to other pages use their slugs as the address (note that these links do not work in the preview, but will on the real site)",
    )

    raw_content = models.TextField(
        "Raw HTML",
        blank=True,
        default='',
        help_text="You can enter raw HTML into this box, and it will be used if 'Enter content as raw HTML' is selected"
    )
    use_raw = models.BooleanField(
        'Enter content as raw HTML',
        default=False,
    )

    featured_image_file = models.ForeignKey(File, blank=True, null=True)

    KIND_PAGE = 'page'
    KIND_BLOG = 'blog'
    KIND_CHOICES = (
        (KIND_BLOG, 'Blog'),
        (KIND_PAGE, 'Page')
    )
    kind = models.CharField(max_length=10, choices=KIND_CHOICES, default=KIND_PAGE)

    # When was this page/post published. Could use updated or created but it
    # makes sense to make this seperate now as it will facilitate queing up
    # posts to be published in future easier.
    publication_date = models.DateTimeField( default=datetime.datetime.now )

    # Link to the categories and tags, use a custom related_name as this model
    # can represent both pages and posts.
    categories = models.ManyToManyField(Category, related_name="entries", blank=True)
    tags       = models.ManyToManyField(Tag,      related_name="entries", blank=True)


    def __unicode__(self):
        return self.title

    def css_class(self):
        return self._meta.model_name

    def name(self):
        return str(self)

    def _clean_html(self, html):
        if not html:
            return ''
        cleaner = Cleaner(style=True, scripts=True)
        return cleaner.clean_html(html)

    @property
    def content_as_html(self):
        if settings.INFO_PAGES_ALLOW_RAW_HTML and self.use_raw:
            # Parsing the HTML with lxml and outputting it again
            # should ensure that we have only well-formed HTML:
            parsed = lxml.html.fromstring(self.raw_content)
            return lxml.etree.tostring(parsed, method='html')
        else:
            # Since there seems to be some doubt about whether
            # markdown's safe_mode is really safe, clean the rendered
            # HTML to remove any potentially dangerous tags first
            return self._clean_html(self.markdown_content.rendered or '')

    @property
    def content_as_cleaned_html(self):
        return self._clean_html(self.content_as_html)

    @property
    def content_as_plain_text(self):
        cleaned_html = self.content_as_cleaned_html
        cleaned_text = lxml.html.fromstring(cleaned_html).text_content()
        return re.sub(r'(?ms)\s+', ' ', cleaned_text).strip()

    def content_with_anchors(self):
        """ Returns content with an anchor tag <a> inserted above every heading element
            (the anchor name is the slugified heading text). For example:
            <h2>Halt! Who goes there?"</h2>
            becomes
            <a name="halt-who-goes-there">
            <h2>Halt! Who goes there?"</h2>"""
        def prepend_anchor_tag( match ):
            return '<a name="%s"></a>%s%s' % (slugify(match.group(2)), match.group(1), match.group(2))
        headings_regexp = re.compile( '(<h\d+[^>]*>)([^<]*)')
        return headings_regexp.sub( prepend_anchor_tag, self.content_as_html)

    @models.permalink
    def get_absolute_url(self):

        if self.kind == self.KIND_PAGE:
            url_name = 'info_page'
        elif self.kind == self.KIND_BLOG:
            url_name = 'info_blog'
        else:
            raise Exception("Unexpected kind '{0}'".format(self.kind))

        return ( url_name, [ self.slug ] )

    def get_admin_url(self):
        url = reverse(
            'admin:%s_%s_change' % ( self._meta.app_label, self._meta.model_name),
            args=[self.id]
        )
        return url

    class Meta:
        ordering = ['title']


class ViewCount(models.Model):
    date = models.DateField()
    page = models.ForeignKey(InfoPage)

    # Keeping a normal integer here just in case we at some point want
    # to manually insert a negative count to keep a post down.
    count = models.IntegerField()

    class Meta:
        unique_together = ('date', 'page')

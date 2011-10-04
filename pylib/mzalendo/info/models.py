import datetime

from django.db import models
from django.core.urlresolvers import reverse
from markitup.fields import MarkupField

class InfoPage(models.Model):
    created = models.DateTimeField( auto_now_add=True, default=datetime.datetime.now(), )
    updated = models.DateTimeField( auto_now=True,     default=datetime.datetime.now(), )    

    slug    = models.SlugField(unique=True)
    title   = models.CharField(max_length=300, unique=True)
    content = MarkupField( help_text="When linking to other pages use their slugs as the address (note that these links do not work in the preview, but will on the real site)")

    def __unicode__(self):
        return self.title

    def name(self):
        return str(self)

    @models.permalink
    def get_absolute_url(self):
        return ( 'info_page', [ self.slug ] )

    def get_admin_url(self):
        url = reverse(
            'admin:%s_%s_change' % ( self._meta.app_label, self._meta.module_name),
            args=[self.id]
        )
        return url

    class Meta:
        ordering = ['title']      

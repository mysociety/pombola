import re

from django.db import models
from django.core.urlresolvers import reverse

from pombola.hansard.models.base import HansardModelBase
from pombola.hansard.models import Source, Venue


class Sitting(HansardModelBase):
    source = models.ForeignKey(Source)
    venue = models.ForeignKey(Venue)
    
    start_date = models.DateField()
    start_time = models.TimeField(blank=True, null=True)
    end_date = models.DateField(blank=True, null=True)
    end_time = models.TimeField(blank=True, null=True)
    
    def __unicode__(self):
        return self.name

    def get_absolute_url(self):
        """Create a url from the venue slug and the start time"""
        start_date_and_time = str( self.start_date )
        if self.start_time:
            start_date_and_time += '-' + str( self.start_time )
            start_date_and_time = re.sub(':','-',start_date_and_time)

        url = reverse(
            'hansard:sitting_view',
            kwargs={
                'venue_slug': self.venue.slug,
                'start_date_and_time': start_date_and_time,
            },
        )

        return url

    @property
    def name(self):
        """Format the times nicely to give a name"""

        # This is ugly code, but I'm not sure it could be made much nicer and
        # still cover most of the variations in a nice to read way.

        ret = ''

        if self.end_date:
            if self.end_date == self.start_date:
                ret = "%s" %self.start_date
                if self.start_time:
                    ret += ": %s" % self.start_time
                    if self.end_time:
                        ret += " to %s" % self.end_time
            else:
                ret += "%s" % self.start_date
                if self.start_time:
                    ret += " %s" % self.start_time
                ret += " to %s" % self.end_date
                if self.end_time:
                    ret += " %s" % self.end_time
        else:
            ret = "%s" % self.start_date
            if self.start_time:
                ret += ": %s" % self.start_time
            if self.end_time:
                ret += " to %s" % self.end_time

        # strip off trailing :00 seconds from times
        ret = re.sub( r':00(\s|$)', r'\1', ret )

        return self.venue.name + ' ' + ret

    class Meta:
        ordering = ['-start_date']
        app_label = 'hansard'



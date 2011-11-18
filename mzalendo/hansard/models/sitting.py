import datetime
import re

from django.db import models
from hansard.models import Source, Venue

class Sitting(models.Model):

    source = models.ForeignKey(Source)
    venue  = models.ForeignKey(Venue)
    
    start_date = models.DateField()
    start_time = models.TimeField( blank=True, null=True )
    end_date   = models.DateField( blank=True, null=True )
    end_time   = models.TimeField( blank=True, null=True )
    
    def __unicode__(self):
        return self.name()


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
        ordering = ['start_date']
        app_label = 'hansard'
        


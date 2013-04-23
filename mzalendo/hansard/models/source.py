import os
import re
import httplib2

from django.db import models
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

from hansard.models.base import HansardModelBase

# check that the cache is setup and the directory exists
try:
    HANSARD_CACHE = settings.HANSARD_CACHE
    if not os.path.exists( HANSARD_CACHE ):
        os.makedirs( HANSARD_CACHE )
except AttributeError:
    raise ImproperlyConfigured("Could not find HANSARD_CACHE setting - please set it")


# EXCEPTIONS

class SourceUrlCouldNotBeRetrieved(Exception):
    pass

class SourceCouldNotParseTimeString(Exception):
    pass




class SourceQuerySet(models.query.QuerySet):
    def requires_processing(self):
        return self.filter( last_processing_attempt=None )


class SourceManager(models.Manager):
    def get_query_set(self):
        return SourceQuerySet(self.model)


class Source(HansardModelBase):
    """
    Sources of the hansard transcripts
    
    For example a PDF transcript.
    """

    name           = models.CharField(max_length=200, unique=True)
    date           = models.DateField()
    url            = models.URLField(max_length=1000)

    last_processing_attempt = models.DateTimeField(blank=True, null=True)
    last_processing_success = models.DateTimeField(blank=True, null=True)

    objects = SourceManager()

    class Meta:
        app_label = 'hansard'
        ordering = [ '-date', 'name' ]

    def __unicode__(self):
        return self.name


    def delete(self):
        """After deleting from db, delete the cached file too"""
        cache_file_path = self.cache_file_path()
        super( Source, self ).delete()
        
        if os.path.exists( cache_file_path ):
            os.remove( cache_file_path )
        
        
    def file(self):
        """
        Return as a file object the resource that the url is pointing to.
        
        Should check the local cache first, and fetch and store if it is not
        found there.
        
        Raises a SourceUrlCouldNotBeRetrieved exception if URL could not be
        retrieved.
        """
        cache_file_path = self.cache_file_path()
        
        # If the file exists open it, read it and return it
        try:
            return open(cache_file_path, 'r')
        except IOError:
            pass # ignore
        
        # If not fetch the file, save to cache and then return fh
        h = httplib2.Http()
        response, content = h.request(self.url)

        # Crude handling of response - is there an is_success method?
        if response.status != 200:
            raise SourceUrlCouldNotBeRetrieved("status code: %s, url: %s" % (response.status, self.url) )

        with open(cache_file_path, "w") as new_cache_file:
            new_cache_file.write(content)        
        
        return open(cache_file_path, 'r')
            

    def cache_file_path(self):
        """Absolute path to the cache file for this source"""

        id_str= "%05u" % self.id

        # do some simple partitioning
        # FIXME - put in something to prevent the test suite overwriting non-test files.
        aaa = id_str[-1]
        bbb = id_str[-2]
        cache_dir = os.path.join(HANSARD_CACHE, aaa, bbb)

        # check that the dir exists
        if not os.path.exists( cache_dir ):
            os.makedirs( cache_dir )
        
        # create the path to the file
        cache_file_path = os.path.join(cache_dir, id_str)
        return cache_file_path

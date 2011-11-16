import os
import httplib2
import xml.sax
import tempfile
import subprocess

from django.db import models
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

from hansard.xml_handlers import HansardXML

# check that the cache is setup and the directory exists
try:
    HANSARD_CACHE = settings.HANSARD_CACHE
    if not os.path.exists( HANSARD_CACHE ):
        os.makedirs( HANSARD_CACHE )
except AttributeError:
    raise ImproperlyConfigured("Could not find HANSARD_CACHE setting - please set it")


class SourceQuerySet(models.query.QuerySet):
    def requires_processing(self):
        return self.filter( last_processed=None )


class SourceManager(models.Manager):
    def get_query_set(self):
        return SourceQuerySet(self.model)


class Source(models.Model):
    """
    Sources of the hansard transcripts
    
    For example a PDF transcript.
    """

    name           = models.CharField(max_length=200, unique=True)
    date           = models.DateField()
    url            = models.URLField()
    last_processed = models.DateField(blank=True, null=True)

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
        found there. Returns none if URL could not be retrieved.
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
        if response.status != 200: return None

        with open(cache_file_path, "w") as new_cache_file:
            new_cache_file.write(content)        
        
        return open(cache_file_path, 'r')
            

    def cache_file_path(self):
        """Absolute path to the cache file for this source"""

        id_str= "%05u" % self.id

        # do some simple partitioning
        aaa = id_str[-1]
        bbb = id_str[-2]
        cache_dir = os.path.join(HANSARD_CACHE, aaa, bbb)

        # check that the dir exists
        if not os.path.exists( cache_dir ):
            os.makedirs( cache_dir )
        
        # create the path to the file
        cache_file_path = os.path.join(cache_dir, id_str)
        return cache_file_path
    
    
    @classmethod
    def covert_pdf_to_html(cls, pdf_file):
        """Given a PDF parse it and return the HTML string representing it"""

        pdftohtml_cmd = 'pdftohtml'

        def run_pdftohtml( args ):
            pdftohtml = subprocess.Popen(
                args,
                shell = False,
                stdout = subprocess.PIPE,
            )

            ( output, ignore ) = pdftohtml.communicate()
            return output

        # get the version number of pdftohtml and check that it is acceptable - see
        # 'hansard/notes.txt' for issues with the output from different versions.
        pdftohtml_version = run_pdftohtml( [ cmd, '-version', pdf_file.name ] )
        wanted_version = 'pdftohtml version 0.12.4'
        if wanted_version not in pdftohtml_version:
            raise Exception( "Bad pdftohtml version - got '%s' but want '%s'" % (pdftohtml_version, wanted_version) )

        return run_pdftohtml( [ cmd, '-stdout', '-noframes', pdf_file.name ] )


    @classmethod
    def convert_html_to_data(cls, html):

        hansard_data = {}

        # print "len of pdftohtml :" + str( len(pdf_as_xml) )
        # 
        # hansard_data = xml.sax.parseString( pdf_as_xml, HansardXML() )
        
        return hansard_data

import httplib2
import os
import re
import subprocess
import tempfile

from django.db import models
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

from hansard.xml_handlers import HansardXML

from BeautifulSoup import BeautifulSoup, BeautifulStoneSoup, NavigableString, Tag

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

        # Clean out all the &nbsp; now. pdftohtml puts them to preserve the lines
        html = re.sub( r'&nbsp;', ' ', html )

        # create a soup out of the html
        soup = BeautifulSoup(
            html,
            convertEntities=BeautifulStoneSoup.HTML_ENTITIES
        )

        contents = soup.body.contents
        br_count = 0

        filtered_contents = []
        
        while len(contents):
            line = contents.pop(0)

            # get the tag name if there is one
            tag_name = line.name if type(line) == Tag else None

            # count <br> tags - we use two or more in succession to decide that
            # we've moved on to a new bit of text
            if tag_name == 'br':
                br_count += 1
                continue

            # skip empty lines
            if tag_name == None:
                text_content = str(line)
            else:
                text_content = line.text
            
            if re.match( r'\s*$', text_content ):
                continue
            
            
            # check for something that looks like the page number - when found
            # delete it and the two lines that follow
            if tag_name == 'b' and re.match( r'\d+\s{10,}', line.text ):
                print "skipping page number line: " + line.text
                while len(contents):
                    item = contents.pop(0)
                    if type(item) == Tag and item.name == 'hr': break
                continue


            # if br_count > 0:
            #     print 'br_count: ' + str(br_count)
            # print type( line )
            # # if type(line) == Tag: print line.name
            # print "%s: >>>%s<<<" % (tag_name, text_content)
            # print '------------------------------------------------------'
            
            filtered_contents.append(dict(
                tag_name     = tag_name,
                text_content = text_content.strip(),
                br_count     = br_count,
            ))

            br_count = 0
                    
        # go through all the filtered_content and using the br_count determine
        # when lines should be merged
        merged_contents = []
        
        for line in filtered_contents:

            # print line            
            br_count = line['br_count']
            
            # Join lines that have the same tag_name and are not too far apart
            if br_count <= 1  and len(merged_contents) and line['tag_name'] == merged_contents[-1]['tag_name']:
                new_content = ' '.join( [ merged_contents[-1]['text_content'], line['text_content'] ] )
                merged_contents[-1]['text_content'] = new_content
            else:
                merged_contents.append( line )
        
        # now go through and create some meaningful chunks from what we see
        meaningful_content = []
        last_speaker = ''

        while len(merged_contents):

            line = merged_contents.pop(0)
            next_line = merged_contents[0] if len(merged_contents) else None

            print '----------------------------------------'
            print line
            print next_line
            

            # if the content is italic then it is a scene
            if line['tag_name'] == 'i':
                meaningful_content.append({
                    'type': 'scene',
                    'text': line['text_content'],
                })
                continue
            
            # if the content is all caps then it is a heading
            if line['text_content'] == line['text_content'].upper():
                meaningful_content.append({
                    'type': 'heading',
                    'text': line['text_content'],
                })
                last_speaker = ''
                continue
                
            # It is a speech if we have a speaker and it is not formatted
            if line['tag_name'] == None and last_speaker:
                meaningful_content.append({
                    'type': 'speech',
                    'speaker': last_speaker,
                    'text': line['text_content'],
                })
                continue

            # If it is a bold line and the next line is 'None' and is no
            # br_count away then we have the start of a speech.
            if line['tag_name'] == 'b' and next_line['tag_name'] == None and next_line['br_count'] == 0:
                last_speaker = line['text_content']
                continue

            meaningful_content.append({
                'type': 'other',
                'text': line['text_content'],
            })
            last_speaker = ''

            


        hansard_data = {
            'transcript': meaningful_content,
        }

        return hansard_data

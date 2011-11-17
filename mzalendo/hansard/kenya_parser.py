import httplib2
import os
import re
import subprocess
import tempfile

from django.db import models
from django.conf import settings

from BeautifulSoup import BeautifulSoup, BeautifulStoneSoup, NavigableString, Tag


# EXCEPTIONS
class KenyaParserCouldNotParseTimeString(Exception):
    pass


class KenyaParser():  
    
    @classmethod
    def convert_pdf_to_html(cls, pdf_file):
        """Given a PDF parse it and return the HTML string representing it"""

        remote_host = settings.KENYA_PARSER_PDF_TO_HTML_HOST
        
        if remote_host:
            return cls.convert_pdf_to_html_remote_machine(pdf_file, remote_host)
        else:
            return cls.convert_pdf_to_html_local_machine( pdf_file )


    @classmethod
    def convert_pdf_to_html_local_machine(cls, pdf_file):
        """Use local pdftohtml binary to convert the pdf to html"""

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
        pdftohtml_version = run_pdftohtml( [ pdftohtml_cmd, '-version', pdf_file.name ] )
        wanted_version = 'pdftohtml version 0.12.4'
        if wanted_version not in pdftohtml_version:
            raise Exception( "Bad pdftohtml version - got '%s' but want '%s'" % (pdftohtml_version, wanted_version) )

        return run_pdftohtml( [ pdftohtml_cmd, '-stdout', '-noframes', '-enc', 'UTF-8', pdf_file.name ] )


    @classmethod
    def convert_pdf_to_html_remote_machine(cls, pdf_file, remote):
        """Convert pdf on a remote machine"""
        
        bin_dir               = os.path.abspath( os.path.dirname( __file__ ) + '/bin' )
        remote_convert_script = os.path.join( bin_dir, 'convert_pdf_to_html_on_remote_machine.bash'  )

        remote_pdftohtml = subprocess.Popen(
            [ remote_convert_script, remote, pdf_file.name ],
            shell = False,
            stdout = subprocess.PIPE,
        )

        ( output, ignore ) = remote_pdftohtml.communicate()
        return output


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

        # counters to use in the loops below
        br_count    = 0
        page_number = 1

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
                text_content = unicode(line)
            else:
                text_content = line.text
            
            if re.match( r'\s*$', text_content ):
                continue
            
            
            # check for something that looks like the page number - when found
            # delete it and the two lines that follow
            if tag_name == 'b':
                page_number_match = re.match( r'(\d+)\s{10,}', line.text )
                if page_number_match:
                    # up the page number - the match is the page that we are leaving
                    page_number = int(page_number_match.group(0)) + 1
                    # skip on to the next page
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
            

            text_content = text_content.strip()
            text_content = re.sub( r'\s+', ' ', text_content )
            
            filtered_contents.append(dict(
                tag_name     = tag_name,
                text_content = text_content,
                br_count     = br_count,
                page_number  = page_number,
            ))

            br_count = 0
                    
        # go through all the filtered_content and using the br_count determine
        # when lines should be merged
        merged_contents = []
        
        for line in filtered_contents:

            # print line            
            br_count = line['br_count']
            
            # Join lines that have the same tag_name and are not too far apart
            if (
                    br_count <= 1
                and len(merged_contents)
                and line['tag_name'] == merged_contents[-1]['tag_name']
            ):
                new_content = ' '.join( [ merged_contents[-1]['text_content'], line['text_content'] ] )
                merged_contents[-1]['text_content'] = new_content
            else:
                merged_contents.append( line )
        
        # now go through and create some meaningful chunks from what we see
        meaningful_content = []
        last_speaker_name  = ''
        last_speaker_title = ''

        while len(merged_contents):

            line = merged_contents.pop(0)
            next_line = merged_contents[0] if len(merged_contents) else None

            # print '----------------------------------------'
            # print line
            

            # if the content is italic then it is a scene
            if line['tag_name'] == 'i':
                meaningful_content.append({
                    'type': 'scene',
                    'text': line['text_content'],
                    'page_number': line['page_number'],
                })
                continue
            
            # if the content is all caps then it is a heading
            if line['text_content'] == line['text_content'].upper():
                meaningful_content.append({
                    'type': 'heading',
                    'text': line['text_content'],
                    'page_number': line['page_number'],
                })
                last_speaker_name  = ''
                last_speaker_title = ''
                continue
                
            # It is a speech if we have a speaker and it is not formatted
            if line['tag_name'] == None and last_speaker_name:

                # do some quick smarts to see if we can extract a name from the
                # start of the speech.
                speech = line['text_content']
                
                matches = re.match( r'\(([^\)]+)\):(.*)', speech )
                if matches:
                    last_speaker_title = last_speaker_name
                    last_speaker_name = matches.group(1)
                    speech = matches.group(2)

                meaningful_content.append({
                    'speaker_name':  last_speaker_name,
                    'speaker_title': last_speaker_title,
                    'text': speech,
                    'type': 'speech',
                    'page_number': line['page_number'],
                })
                
                # print meaningful_content[-1]
                
                continue

            # If it is a bold line and the next line is 'None' and is no
            # br_count away then we have the start of a speech.
            if (
                    line['tag_name']      == 'b'
                and next_line['tag_name'] == None
                and next_line['br_count'] == 0
            ):
                last_speaker_name = line['text_content'].strip(':')
                last_speaker_title = ''
                continue

            meaningful_content.append({
                'type': 'other',
                'text': line['text_content'],
                'page_number': line['page_number'],
            })
            last_speaker_name  = ''
            last_speaker_title = ''

        hansard_data = {
            'meta': cls.extract_meta_from_transcript( meaningful_content ),
            'transcript': meaningful_content,
        }

        return hansard_data



    @classmethod
    def extract_meta_from_transcript(cls, transcript):
        reg = re.compile(r"The House (?P<action>met|rose) at (?P<time>\d+\.\d+ [ap].m.)")

        results = {}

        for line in transcript:
            text = line.get('text', '')
            
            match = reg.match(text)
            if not match: continue

            groups = match.groupdict()

            hhmm = cls.parse_time_string( groups['time'] )
                        
            if groups['action'] == 'met':
                results['start_time'] = hhmm
            else:
                results['end_time'] = hhmm
            
        return results


    @classmethod
    def parse_time_string(cls, time_string):
        """Given a string input return HH:MM:SS format string, or raises SourceCouldNotParseTimeString if it can't be done"""

        # A quick google did not reveal a generic time parsing library, although
        # there must be one.

        time_regex = re.compile( r'(\d+)\.(\d+) (a|p)')
        match = time_regex.match(time_string)
        
        if not match:
            raise KenyaParserCouldNotParseTimeString( "bad time string: '%s'" % time_string )
        
        hour, minute, am_or_pm = match.groups()

        hour   = int(hour)
        minute = int(minute)
        

        if am_or_pm == 'p' and hour < 12:
            hour += 12 

        return '%02u:%02u:00' % (hour,minute)
        












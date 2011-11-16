import re
import logging
logging.basicConfig()

from xml.sax.handler import ContentHandler





class HansardXML(ContentHandler):

    feature_external_pes = False

    def __init__(self, *args, **kwargs):
        
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel( logging.DEBUG )
        

        # counters and state indicators
        self.text_counter          = 0
        self.current_text_counter  = 0
        self.page_counter  = 0
        self.is_bolded     = False
        self.is_italic     = False

        self.should_ignore      = True
        self.should_store_chunk = False
        
        self.content_chunks  = []
        self.content_buffers = {
            'plain' : [],
            'bold'  : [],
            'italic': [],
        }

        # put a blank chunk at the start
        # self.store_chunk()
        

    def characters(self, content):
        """Gather all the content onto a buffer"""
        
        if self.should_ignore:
            self.logger.debug( "IGNORING '%s'" % content )
            return
            
        # Determine if we have started a new chunk
        if re.match( r'\s*$', content ):
            self.logger.debug( "set should_store_chunk = True" )
            self.should_store_chunk = True
            
        self.logger.debug( "'%s'" % content             )
        self.append_to_buffer( content )

    def startElement(self, name, attr):
        self.logger.debug( '--- start %s ---' % name )
        # self.logger.debug( attr.items() )

        # Increment the counters
        if name == 'text':
            self.text_counter += 1
            if not self.current_text_counter: self.current_text_counter = self.text_counter

        if name == 'page': self.page_counter += 1

        # Update the state flags
        if name == 'b': self.is_bolded = True
        if name == 'i': self.is_italic = True

        if name in ['b','i']:
            self.store_chunk()

        # Ignore headers and footers
        if name == 'text' and int(attr.get('top', 0)) < 720:
            self.should_ignore = False


    def endElement(self, name):
        self.logger.debug( '--- end %s ---' % name )

        # Update the state flags
        if name == 'b': self.is_bolded = False
        if name == 'i': self.is_italic = False

        # At the end of text start ignoring
        if name == 'text':
            self.should_ignore = True
            if self.should_store_chunk:
                self.store_chunk()
    
    def endDocument(self):
        """docstring for endDocument"""
        self.store_chunk()
    

    def flatten_content(self):
        content = {}

        self.logger.debug( self.content_buffers )

        for k in self.content_buffers.keys():
            raw_content  = ''.join( self.content_buffers[k] )
            tidy_content = re.sub(r'\s+',' ', raw_content )
            tidy_content = tidy_content.strip()
            content[k] = tidy_content
            self.content_buffers[k] = []
        
        return content


    def store_chunk(self):
        """Store the current chunk"""
        chunk = {
            'page': self.page_counter,
        }

        chunk['text_counter'] = self.current_text_counter or self.text_counter
        self.current_text_counter = None

        content = self.flatten_content()

        if content['plain'] and content['bold']:
            chunk['type'] = 'speech'
            chunk['speaker']  = content.pop('bold')
            chunk['content'] = content.pop('plain')
        elif content['italic']:
            chunk['type'] = 'event'
            chunk['content'] = content.pop('italic')
        elif content['bold']:
            chunk['type'] = 'heading'
            chunk['content'] = content.pop('bold')
        else:
            chunk['type'] = 'unknown'
            chunk['content'] = content.pop('plain')

        # check that no content has been forgotten
        for k in content.keys():
            if not content[k]: continue
            self.logger.warning("Missed content in '%s': %s" % ( k, content[k] ) )
            chunk['content'] += content[k]

        if chunk['content']:
            self.content_chunks.append(chunk)

        self.should_store_chunk = False

        
    def append_to_buffer(self, content):
        """Add the content to the correct buffer"""
        if   self.is_bolded: buffer_name = 'bold'
        elif self.is_italic: buffer_name = 'italic'
        else:                buffer_name = 'plain'
        
        self.content_buffers[buffer_name].append( content )


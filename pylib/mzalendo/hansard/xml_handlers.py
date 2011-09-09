import re


from xml.sax.handler import ContentHandler

class HansardXML(ContentHandler):
    def __init__(self, *args, **kwargs):

        # counters and state indicators
        self.text_counter  = 0
        self.page_counter  = 0
        self.is_bolded     = False
        self.is_italic     = False
        self.should_ignore = False
        
        self.content_chunks = []
        self.content_buffer = []


    def characters(self, content):
        """Gather all the content onto a buffer"""
        
        if self.should_ignore:
            # print "IGNORING '%s'" % content
            return
            
        print "'%s'" % content            
        self.content_buffer.append( content )

        # Determine if we have started a new chunk
        if self.is_bolded:
            self.store_chunk()
        
    def startElement(self, name, attr):
        print '--- start %s ---' % name
        # print attr.items()

        # Increment the counters
        if name == 'text': self.text_counter += 1
        if name == 'page': self.page_counter += 1

        # Update the state flags
        if name == 'b': self.is_bolded = True
        if name == 'i': self.is_italic = True

        # Ignore headers and footers
        if name == 'text' and int(attr.get('top', 0)) > 720:
            self.should_ignore = True
        else:
            self.should_ignore = False


    def endElement(self, name):
        print '--- end %s ---' % name

        # Update the state flags
        if name == 'b': self.is_bolded = False
        if name == 'i': self.is_italic = False

        # At the end of text start ignoring
        if name == 'text': self.should_ignore = True
    

    def store_chunk(self):
        """Store the current chunk"""
        content = re.sub(r'\s+',' ', ''.join(self.content_buffer) )
        
        chunk = {
            'content': content
        }
        
        self.content_chunks.append(chunk)
        self.content_buffer = []
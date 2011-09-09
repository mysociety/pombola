from xml.sax.handler import ContentHandler

class HansardXML(ContentHandler):
    def __init__(self, *args, **kwargs):

        # counters and state indicators
        self.text_counter  = 0
        self.page_counter  = 0
        self.is_bolded     = False
        self.is_italic     = False
        self.should_ignore = False
        
        self.data = {}
        self.content_buffer = ''

    def characters(self, content):
        """Gather all the content onto a buffer"""
        if not self.should_ignore:
            self.content_buffer += content
            # print self.content_buffer
        else:
            print "IGNORING '%s'" % content            

    def startElement(self, name, attr):
        print '--- start %s ---' % name
        print attr.items()

        # Increment the counters
        if name == 'text': self.text_counter += 1
        if name == 'page': self.page_counter += 1

        # Update the state flags
        if name == 'b': self.is_bolded = True
        if name == 'i': self.is_italic = True

        # Ignore headers and footers

        if name == 'text' and int(attr.get('top', 0)) > 720:
            self.should_ignore = True

    def endElement(self, name):
        print '--- end %s ---' % name

        # Update the state flags
        if name == 'b': self.is_bolded = False
        if name == 'i': self.is_italic = False

        # At the end of text stop ignoring
        if name == 'text': self.should_ignore = False
    

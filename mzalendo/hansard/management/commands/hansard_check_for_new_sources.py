import pprint
import httplib2
import re
import datetime
import sys

from BeautifulSoup import BeautifulSoup, BeautifulStoneSoup

from django.conf import settings


from django.core.management.base import NoArgsCommand

from hansard.models import Source

class Command(NoArgsCommand):
    help = 'Check for new sources'

    # Manually list all the urls that we should check here. These are all the
    # entries in the 'Hansard' tab: http://www.parliament.go.ke/
    parliament_base_url = "http://www.parliament.go.ke"
    full_url_format = parliament_base_url + "/index.php?option=com_content&view=article&id=%u&Itemid=%u"
    listing_pages = {
        2006: full_url_format % ( 202, 165 ),
        2007: full_url_format % ( 188, 161 ),
        2008: full_url_format % ( 89,  82  ),
        2009: full_url_format % ( 90,  83  ),
        2010: full_url_format % ( 91,  84  ),
        2011: full_url_format % ( 184, 159 ),
        2012: full_url_format % ( 243, 206 ),
    }
    
    def handle_noargs(self, **options):

        self.check_we_have_a_current_listing_url()

        for year, url in self.listing_pages.items():
            # print 'scraping %s listing url: %s' % (year, url)
            self.get_urls_from_listing_page( url )


    def get_urls_from_listing_page(self, url):
        h = httplib2.Http( settings.HTTPLIB2_CACHE_DIR )
        response, content = h.request(url)
        # print content
        
        # parse content
        soup = BeautifulSoup(
            content,
            convertEntities=BeautifulStoneSoup.HTML_ENTITIES
        )

        links = soup.findAll( 'a', 'doclink')

        for link in links:

            # print dir(link)
            # import pdb; pdb.set_trace()

            href = self.parliament_base_url + link['href'].strip()
            name = ' '.join( [ x.string for x in link.contents[1:] ] )

            # get rid of '(123kb)' and trim
            name = re.sub( r'\(.*?\)', '', name ).strip()

            if not name:
                continue

            # print "url: " + href
            # print "name: " + name



            # Extract the date
            date_match = re.search( r'(\d{1,2})\.(\d{1,2})\.(\d{2,4})', name)
            if not date_match:
                continue
                
            (dd,mm,yy) = map(
                lambda xx: int(xx),
                date_match.groups()
            )

            # check that our two digit date assumption remains sane
            if yy <= 99: yy = yy + 2000
            assert yy <= datetime.date.today().year, "year %u is too large - might be pre 2000?" % yy

            source_date = datetime.date(yy, mm, dd)
            # print source_date

            # create/update the source entry
            Source.objects.get_or_create(
                name = name,
                defaults = dict(
                    url = href,
                    date = source_date,
                )
            )
                
    def check_we_have_a_current_listing_url(self):
        """check that we have a listing url for the current year, if not warn to logs"""

        yyyy = datetime.date.today().year
        if yyyy not in self.listing_pages:
            sys.stderr.write("Don't have a url for the %s hansard transcripts - please add to %s\n\n" % (yyyy, __file__))

# This script was first changed extensively when the Kenyan Parliament website
# changed after the 2013 Election.
#
# The pre-2013 Election version can be seen at:
#
#    https://github.com/mysociety/pombola/blob/7181e30519b140229e3817786e4a7440ac08288d/mzalendo/hansard/management/commands/hansard_check_for_new_sources.py
#
# It was then changed again after the Kenyan Parliament website was
# given an overhaul during the Christmas 2014 break.
#
# The previous version can be seen at:
#
#    https://github.com/mysociety/pombola/blob/ec4a44f7d7e0743426aff87b59e4bfa54250ec1c/pombola/hansard/management/commands/hansard_check_for_new_sources.py

import httplib2
import re
import datetime
from optparse import make_option
import parsedatetime as pdt
from warnings import warn
from urlparse import urlsplit, urlunsplit

from BeautifulSoup import BeautifulSoup, BeautifulStoneSoup

from django.conf import settings


from django.core.management.base import NoArgsCommand

from pombola.hansard.models import Source

def fix_date_text(date_text):
    return re.sub(r'Octoer', 'October', date_text)

class NoSourcesFoundError(Exception):
    pass

class Command(NoArgsCommand):
    help = 'Check for new sources'

    # http://www.parliament.go.ke
    # /plone/national-assembly/business/hansard/copy_of_official-report-28-march-2013-pm/at_multi_download/item_files
    # ?name=Hansard%20National%20Assembly%2028.03.2013P.pdf

    option_list = NoArgsCommand.option_list + (
        make_option('--check-all', action='store_true',
                    help='Carry on to check sources on every page'),
    )

    def handle_noargs(self, **options):

        self.options = options
        verbose = int(options.get('verbosity')) >= 2

        for list_page, url in (
            ('senate',
             'http://www.parliament.go.ke/index.php/the-senate/house-business/hansard'),
            ('national-assembly',
             'http://www.parliament.go.ke/index.php/the-national-assembly/house-business/hansard'),
        ):
            try:
                self.process_url(list_page, url, verbose)
            except NoSourcesFoundError:
                warn("Could not find any Hansard sources on '%s'" % url)


    def process_url(self, list_page, url, verbose):
        """
        For the given url find or create an entry for each source in the database.

        If no sources found raise an exception.
        """

        # using the pagination links on the list pages themselves, iterate
        # over all the list pages until we're up to date (hopefully needing
        # to go beyond page 1 will be a rare occurence, mostly reserved for
        # when the scraper hasn't run for a while such as a major update to
        # the target site necessitating a adjustment to this script)

        for soup, base_url in self.get_index_pages(url, list_page, verbose):
            # Grab each of the blocks on the current page which are supposed
            # to contain a link to a PDF file.
            link_sections = soup.findAll('span', 'file--application-pdf')

            links = [section.a for section in link_sections]

            # Check that we found some links. This is to detect when the page
            # changes or our scraper breaks (see issue #905 for example).
            # Checking that the most recent source is not more that X weeks
            # old might also be a good idea, but could lead
            # to lots of false positives as there is often a long hiatus.
            if not len(links):
                raise NoSourcesFoundError()

            for idx, link in enumerate(links):
                # print '==============='
                # print link

                href = link['href'].strip()
                # print "href: " + href

                name = link.text.strip()
                # print "name: " + name

                if Source.objects.filter(
                    list_page=list_page,
                    name=name,
                ).exists():
                    if verbose:
                        message = "{0}: Skipping page with name: {1}"
                        print message.format(list_page, name)
                    get_next_page = False
                else:
                    if verbose:
                        message = "{0} Trying to add page with name {1} as a new source"
                        print message.format(list_page, name)
                    get_next_page = True

                    self.extract_source_from_html(href, name, list_page, links, link_sections, idx, base_url)

            # Stop scraping list pages if the last source link on the page has
            # already been processed (potentially fragile if we lose the link
            # to the server part way through as this gives us no means of
            # moving beyond the first page if, for example, page 1 has been
            # processed but pages 2 and 3 have not)
            if not (get_next_page or self.options['check_all']):
                break


    def extract_source_from_html(self, href, name, list_page, links, link_sections, idx, base_url):
        download_url = self.format_url(href.strip(), base_url)
        # print download_url

        cal = pdt.Calendar()
        # Sometimes the space is missing between before the
        # month, so insert that if it appears to be missing:
        tidied_name = re.sub(r'(\d+(st|nd|rd|th))(?=[^ ])', '\\1 ', name)
        # Commas in the name confuse parsedatetime, so strip
        # them out too:
        tidied_name = re.sub(r',', '', tidied_name)
        # Sometimes there are extra spaces - which also
        # confuse parsedatetime, so strip them out as well:
        tidied_name = ' '.join(tidied_name.split())
        tidied_name = fix_date_text(tidied_name)
        result = cal.parseDateText(tidied_name)
        source_date = datetime.date(*result[:3])
        # print "source_date: " + str(source_date)

        # create the source entry
        Source.objects.create(
            name = name,
            url = download_url,
            date = source_date,
            list_page = list_page,
        )


    def get_index_pages(self, url, list_page, verbose):
        h = httplib2.Http( settings.HTTPLIB2_CACHE_DIR )
        next_url = url
        i = 0

        while next_url:
            if verbose:
                i+=1
                message = "\nAttempting to get list page {0} for {1}"
                print message.format(i, list_page)
            response, content = h.request(next_url)

            # parse content
            soup = BeautifulSoup(
                content,
                convertEntities=BeautifulStoneSoup.HTML_ENTITIES
            )

            url_parts = urlsplit(next_url)
            base_url = urlunsplit((url_parts.scheme, url_parts.netloc, '', '', ''))

            next_url = self.get_next_url(soup, url)

            yield soup, base_url


    def format_url(self, url, base_url):
        if url[0] == '/':
            return base_url + url
        else:
            return url


    def get_next_url(self, soup, url):
        next_page_button = soup.find('li', 'pager__item--next')
        if next_page_button.a:
            return ''.join([url, next_page_button.a['href'].strip()])
        else:
            return None

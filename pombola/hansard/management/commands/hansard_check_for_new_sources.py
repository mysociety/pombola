
# This script changed extensively when the Kenyan Parliament website changed after the 2013 Election.
#
# The previous version can be seen at:
#
#    https://github.com/mysociety/pombola/blob/7181e30519b140229e3817786e4a7440ac08288d/mzalendo/hansard/management/commands/hansard_check_for_new_sources.py

import pprint
import httplib2
import re
import datetime
import sys
import parsedatetime as pdt

from BeautifulSoup import BeautifulSoup, BeautifulStoneSoup

from django.conf import settings


from django.core.management.base import NoArgsCommand

from pombola.hansard.models import Source

class Command(NoArgsCommand):
    help = 'Check for new sources'

    # http://www.parliament.go.ke
    # /plone/national-assembly/business/hansard/copy_of_official-report-28-march-2013-pm/at_multi_download/item_files
    # ?name=Hansard%20National%20Assembly%2028.03.2013P.pdf


    def handle_noargs(self, **options):

        url = 'http://www.parliament.go.ke/plone/national-assembly/business/hansard'

        h = httplib2.Http( settings.HTTPLIB2_CACHE_DIR )
        response, content = h.request(url)
        # print content

        # parse content
        soup = BeautifulSoup(
            content,
            convertEntities=BeautifulStoneSoup.HTML_ENTITIES
        )

        spans = soup.findAll( 'span', 'contenttype-repositoryitem')

        links = [ span.a for span in spans ]

        for link in links:


            # print '==============='
            # print link

            href = link['href'].strip()
            # print "href: " + href

            name = ' '.join(link.contents).strip()
            # print "name: " + name


            cal = pdt.Calendar()
            result = cal.parseDateText(name)
            source_date = datetime.date(*result[:3])
            # print "source_date: " + str(source_date)


            # I don't trust that we can accurately create the download link url with the
            # details that we have. Instead fetche the page and extract the url.
            download_response, download_content = h.request(href)
            download_soup = BeautifulSoup(
                download_content,
                convertEntities=BeautifulStoneSoup.HTML_ENTITIES
            )
            download_url = download_soup.find( id="archetypes-fieldname-item_files" ).a['href']
            # print download_url

            # create/update the source entry
            Source.objects.get_or_create(
                name = name,
                defaults = dict(
                    url = download_url,
                    date = source_date,
                )
            )

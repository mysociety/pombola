from datetime import datetime
from urlparse import urljoin

import requests
from bs4 import BeautifulSoup

from django.core.management import BaseCommand

from pombola.core.models import PopoloPerson, ParliamentarySession
from pombola.bills.models import Bill

# These are the URLs we want to scrape bill information from,
# grouped by the slug for the ParliamentarySession they refer to
URLS = {
    's2013': (
        'http://kenyalaw.org/kl/index.php?id=4248',
        'http://kenyalaw.org/kl/index.php?id=4249'
    ),
    'na2013': (
        'http://kenyalaw.org/kl/index.php?id=4250',
        'http://kenyalaw.org/kl/index.php?id=4251'
    ),
}

# There are a couple of typos in the dates on the site, so patch 'em up
DATE_FIXES = {
    "14/05/204": "14/05/2014",
    "30/05/204": "30/05/2014",
    "03/03/214": "03/03/2014",
    "12/072013": "12/07/2013",
}

# Similarly, some sponsor names have typos or are formatted in a way
# that means loose_match_name won't find the correct match. This
# mapping ensures the correct person is found, even if the 'correct'
# names aren't always accurate. For example,
#   Person.objects.loose_match_name("Anyang' Nyong'o")
# will return None, but
#   Person.objects.loose_match_name("Anyang' Nyong")
# will correctly find the Person whose name is "Anyang' Nyong'o"
SPONSOR_FIXES = {
    u"Adan Duale": u"Aden Duale",
    u"Aden Dualle": u"Aden Duale",
    u"Hon. Aden Duale": u"Aden Duale",
    u"Mutula Kilonzo Junior": u"Mutula Kilonzo Jnr",
    u"Rachel Nyamai": u"Rachael Kaki Nyamai",
    u"Stephen Sang": u"Stephen Kipyego Sang",
    u"S. Amos Wako": u"Amos Wako",
    u"S.A. Wako": u"Amos Wako",
    u"Boni Khalwale": u"Bonny Khalwale",
    u"Anyang' Nyong'o": u"Anyang' Nyong",
    u"Agnes Zani": u"Agnes Nzani",
    u"G. G. Kariuki": u"GG Kariuki",
    u"W.K. Ottichilo": u"Wilber Ottichilo Khasilwa",
    u"Kimani Ichung'wah": u"Anthony Kimani Ichung",
    u"Chris Wamalwa": u"Chrisantus Wamalwa Wakhungu",
    u"Wafula Wamunyinyi": u"Athanas M Wafula Wamunyinyi",
}
# There is at least one name that will always return None from
# loose_match_name because it matches several other names.
# In this case, force a lookup to be made via slug
SPONSOR_SLUGS = {
    u"Wanjiku Muhia": "wanjiku-muhia",
}

class Command(BaseCommand):
    help = "Scrapes Senate and National Assembly bills for 2013 & 2014 from kenyalaw.org"

    def handle(self, **kwargs):
        for slug, urls in URLS.items():
            session = ParliamentarySession.objects.get(slug=slug)
            for url in urls:
                self.scrape_url(url, session)

    def scrape_url(self, url, session):
        """
        Scrapes all bill info from the provided URL and creates a Bill model
        for each in the given ParliamentarySession.
        """
        response = requests.get(url)
        soup = BeautifulSoup(response.text, "lxml")
        table = soup.find(class_="page-content").find("table")
        bills = []
        for row in table.find_all("tr")[1:]:
            tds = row.find_all("td")
            title = tds[1].find("a").text
            source_url = urljoin(url, tds[1].find("a")['href'])
            # Fix up some weird chars that cause UnicodeEncodeErrors
            date_string = tds[3].text.strip()
            # If this date is one that we know is invalid, replace it
            # with the correct one before attempting to parse
            date_string = DATE_FIXES.get(date_string, date_string)
            date = datetime.strptime(date_string, u"%d/%m/%Y").date()
            sponsor_name = tds[2].text.split(",")[0].strip()
            # There are some known bad/non-matching names, so if this is one
            # then replace it with the correct string before searching
            sponsor_name = SPONSOR_FIXES.get(sponsor_name, sponsor_name)
            sponsor = Person.objects.loose_match_name(sponsor_name)
            # If the sponsor wasn't found, we might be able to look up
            # the Person via the slug field
            if sponsor is None and sponsor_name in SPONSOR_SLUGS:
                try:
                    sponsor = Person.objects.get(slug=SPONSOR_SLUGS[sponsor_name])
                except Person.DoesNotExist:
                    pass
            if not sponsor:
                print u"WARNING: Couldn't find a match for sponsor name '{0}'." \
                      u" Skipping bill '{1}'".format(sponsor_name, title)
                continue
            bills.append(Bill(
                title=title,
                source_url=source_url,
                date=date,
                parliamentary_session=session,
                sponsor=sponsor
            ))
        Bill.objects.bulk_create(bills)

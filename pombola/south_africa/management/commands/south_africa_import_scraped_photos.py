""" Loop through images in a directory and attempt to match them to a person."""

import re
import os

from django.core.exceptions import ObjectDoesNotExist
from django.core.exceptions import MultipleObjectsReturned
from django.core.management.base import LabelCommand

from django.core.files import File

from django.utils.text import slugify

from pombola.core.models import (
    PopoloPerson, ContentType, Image
)

from haystack.query import SearchQuerySet

# Pretty colours to make it easier to spot things.
BRIGHT = '\033[95m'
ENDC = '\033[0m'

def match_person(name):
    """ Match up a person by name with their database entry. """

    slug = slugify(name)

    # Try match on the name first
    try:
        person = Person.objects.get(legal_name__iexact=name)
    except ObjectDoesNotExist:
        try:
            person = Person.objects.get(slug=slug)
        except ObjectDoesNotExist:
            search = SearchQuerySet().models(Person).filter(text=name)
            if len(search) == 1 and search[0]:
                person = search[0].object
            else:
                return None

    except MultipleObjectsReturned:
        print 'Multiple people returned for ' + name + ' (' + slug + '). Cannot continue.'
        exit(1)

    return person

class Command(LabelCommand):

    help = 'Imports scraped photos from the ZA parliament site, and matches them to people.'

    def __init__(self, *args, **kwargs):
        super(Command, self).__init__(*args, **kwargs)

        self.content_type_person = ContentType.objects.get_for_model(Person)

    def handle_label(self, path, **options):

        matched = 0
        unmatched = 0

        for filename in os.listdir(path):

            # Strip out the .jpg
            name = re.sub('\.jpg', '', filename)

            # Strip any non-alpha trailing characters
            name = re.sub('[^a-zA-Z]*$', '', name)

            # Strip any more trailing whitespace that may have snuck in
            name = name.strip()

            # Make the name unicode so we can actually work with it in the DB
            name = unicode(name)

            # Slice the name into two
            name = name.split('_')

            if len(name) == 2:

                # Match up the person
                person = match_person(name[1] + ' ' + name[0])

                if person is None:
                    print BRIGHT + 'Unable to match "' + filename + '" to a person!'+ ENDC
                    unmatched += 1
                else:
                    print 'Matched ' + person.name.encode('utf-8')

                    Image.objects.create(
                        object_id=person.id,
                        content_type=self.content_type_person,
                        is_primary=True,
                        source='http://www.parliament.gov.za',
                        image=File(open(path + filename, 'r'))
                    )

                    matched += 1

            else:

                # This name doesn't have two bits, complain.
                print BRIGHT + '"' + filename + '" does not parse to a first and last name.'+ ENDC
                unmatched += 1

        print 'Done! Matched ' + str(matched) + ', failed to match ' + str(unmatched)

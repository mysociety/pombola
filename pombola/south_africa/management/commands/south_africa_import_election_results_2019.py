import re

import unicodecsv as csv

from django.core.exceptions import ObjectDoesNotExist
from django.core.exceptions import MultipleObjectsReturned
from django.core.management.base import LabelCommand

from django.utils.text import slugify

from django_date_extensions.fields import ApproximateDate

from pombola.core.models import (
    Person, Organisation, OrganisationKind, Place, PositionTitle, Contact, ContactKind, ContentType
)

# Pretty colours to make it easier to spot things.
HEADER = '\033[95m'
ENDC = '\033[0m'

def parse_approximate_date(s):
    """Take a partial ISO 8601 date, and return an ApproximateDate for it

    >>> ad = parse_approximate_date('2014-02-17')
    >>> type(ad)
    <class 'django_date_extensions.fields.ApproximateDate'>
    >>> ad
    2014-02-17
    >>> parse_approximate_date('2014-02')
    2014-02-00
    >>> parse_approximate_date('2014')
    2014-00-00
    """

    for regexp in [
        r'^(\d{4})-(\d{2})-(\d{2})$',
        r'^(\d{4})-(\d{2})$',
        r'^(\d{4})$'
    ]:
        m = re.search(regexp, s)
        if m:
            return ApproximateDate(*(int(g, 10) for g in m.groups()))
    if s == 'future':
        return ApproximateDate(future=True)
    raise Exception, "Couldn't parse '{0}' as an ApproximateDate".format(s)

class Command(LabelCommand):

    help = 'Imports South Africa election results from CSV.'

    def __init__(self, *args, **kwargs):
        super(Command, self).__init__(*args, **kwargs)

        self.contact_kind_phone = ContactKind.objects.get(slug='phone')
        self.content_type_person = ContentType.objects.get_for_model(Person)

        self.organisation_executive = Organisation.objects.get(slug='national-executive')
        self.organisation_assembly = Organisation.objects.get(slug='national-assembly')
        self.organisation_ncop = Organisation.objects.get(slug='ncop')

    def match_person(self, name):
        """ Match up a person with their database entry, or create a new one. """

        slug = slugify(name)

        # Try match on the name first
        try:
            person = Person.objects.get(legal_name__iexact=name)
        except ObjectDoesNotExist:
            print 'Unable to match ' + name + ' by name, trying by slug'
            try:
                person = Person.objects.get(slug=slug)
            except ObjectDoesNotExist:
                print 'Unable to match ' + name + ' by slug, creating a new person'
                person = Person.objects.create(legal_name=name, slug=slug)

        except MultipleObjectsReturned:
            print 'Multiple people returned for ' + name + ' (' + slug + '). Cannot continue.'
            exit(1)

        return person

    def match_position_title(self, title):
        """ Find a position title by name, or create one. """

        slug = slugify(title)

        position, created = PositionTitle.objects.get_or_create(slug=slug)

        if created:
            position.name = title
            position.save()
            print 'Created new position ' + slug + " as " + title

        return position

    def match_organisation(self, name, kind = None):
        """ Find an organisation by name, or create one. """

        slug = slugify(name)

        if kind:
            kind = OrganisationKind.objects.get(slug=kind)
            organisation, created = Organisation.objects.get_or_create(slug=slug, kind=kind)
        else:
            organisation, created = Organisation.objects.get_or_create(slug=slug)

        if created:
            organisation.name = name
            organisation.save()
            print 'Created new organisation' + slug + " as " + name

        return organisation

    def match_place(self, name):
        """ Match up a place with its database entry, or create a new one. """

        slug = slugify(name)

        place, created = Place.objects.get_or_create(slug=slug)

        if created:
            place.name = name
            place.save()
            print 'Created new place ' + slug + " as " + name

        return place

    def save_contact_list(self, contact, person, contact_kind):

        contact = contact.strip()

        # We might already have this, so get_or_create
        contact_object, created = Contact.objects.get_or_create(
            value = contact.strip(),
            object_id = person.id,
            content_type = self.content_type_person,
            kind = contact_kind,
        )

    def read_file(self, file):
        """ Deal with the business of actually iterating over a file and passing the lines to a function. """

        print HEADER + 'Importing from ' + file + ENDC

        with open(self.path + file) as f:

            # Use a DictReader so this is a bit more futureproof if the CSV changes.
            data = csv.DictReader(f)

            # Iterate over the data, call the function given.
            for person_csv in data:
                yield person_csv

    def import_executive(self, person_csv):
        """ Import data for the Executive. """

        # Find the person
        person = self.match_person(person_csv['First names'].strip() + ' ' + person_csv['Surname'].strip())

        # If the person has a preferred name, set it
        if person_csv['Preferred Name']:
            person.add_alternative_name(person_csv['Preferred Name'], True)

        # Find the position title
        position_title = self.match_position_title(person_csv['Position Title'])

        # Get the position if it already exists, if not create it
        position, created = person.position_set.get_or_create(
            title=position_title,
            organisation=self.organisation_executive,
            start_date=parse_approximate_date(person_csv['Start Date'])
        )

        # Set the things that weren't used to match
        position.category = 'political'
        position.end_date = parse_approximate_date(person_csv['End Date'])

        # Save the new position
        position.save()

    def import_assembly(self, person_csv):
        """ Import data for the Assembly. """

        # Find the person
        person = self.match_person(person_csv['First names'].strip() + ' ' + person_csv['Surname'].strip())

        # This person might have a title; if so set it
        if person_csv['Title']:
            person.title = person_csv['Title']
            person.save()

        # Find the position title
        position_title = self.match_position_title(person_csv['Position Title'])

        # Find the place, assuming it is set
        if person_csv['Place']:
            place = self.match_place(person_csv['Place'])
        else:
            place = None

        # Get the position if it already exists, if not create it
        position, created = person.position_set.get_or_create(
            title=position_title,
            organisation=self.organisation_assembly,
            place=place,
            start_date=parse_approximate_date(person_csv['Start Date'])
        )

        # Set the things that weren't used to match
        position.category = 'political'
        position.end_date = parse_approximate_date(person_csv['End Date'])

        # Save the new position
        position.save()

    def import_mpls(self, person_csv):
        """ Import MPLs. """

        # Find the person
        person = self.match_person(person_csv['First Name'].strip() + ' ' + person_csv['Last Name'].strip())

        # This person might have phone numbers; if so set it
        if person_csv['Cell phone']:
            self.save_contact_list(person_csv['Cell phone'], person, self.contact_kind_phone)

        # If the person has a preferred name, set it
        if person_csv['Preferred Name']:
            person.add_alternative_name(person_csv['Preferred Name'], True)

        # Find the position title.
        position_title = self.match_position_title(person_csv['Position Title'])

        # Find the organisation
        organisation = self.match_organisation(person_csv['Organisation'], 'provincial-legislature')

        # Find the place
        place = self.match_place(person_csv['Place name'])

        # Get the position if it already exists, if not create it
        position, created = person.position_set.get_or_create(
            title=position_title,
            organisation=organisation,
            place=place,
            start_date=parse_approximate_date(person_csv['Start Date'])
        )

        # Set the things that weren't used to match
        position.category = 'political'
        position.end_date = parse_approximate_date(person_csv['End Date'])

        # Save the new position
        position.save()

    def import_ncop(self, person_csv):
        """ Import NCOP members. """

        # Find the person
        person = self.match_person(person_csv['First names'].strip() + ' ' + person_csv['Surname'].strip())

        # This person might have a title; if so set it
        if person_csv['Title']:
            person.title = person_csv['Title']
            person.save()

        # This person might have phone numbers; if so set it
        if person_csv['Cell Phone']:
            self.save_contact_list(person_csv['Cell Phone'], person, self.contact_kind_phone)

        # Find the position title.
        position_title = self.match_position_title(person_csv['Position Title'])

        # Find the place, assuming it is set
        if person_csv['Place Name']:
            place = self.match_place(person_csv['Place Name'])
        else:
            place = None

        # Get the position if it already exists, if not create it
        position, created = person.position_set.get_or_create(
            title=position_title,
            organisation=self.organisation_ncop,
            place=place,
            start_date=parse_approximate_date(person_csv['Start Date'])
        )

        # Set the things that weren't used to match
        position.category = 'political'
        position.end_date = parse_approximate_date(person_csv['End Date'])

        # Save the new position
        position.save()

    def import_iec_assignment(self, person_csv):
        """ Import IEC seat assignments. """

        # Find the person
        person = self.match_person(person_csv['Name'].strip() + ' ' + person_csv['Surname'].strip())

        # Find the position title.
        position_title = self.match_position_title(person_csv['Position Title'])

        # Find the place, assuming it is set
        if person_csv['Place Name']:
            place = self.match_place(person_csv['Place Name'])
        else:
            place = None

        # Find the organisation
        organisation = self.match_organisation(person_csv['Organisation'])

        # Get the position if it already exists, if not create it
        position, created = person.position_set.get_or_create(
            title=position_title,
            organisation=organisation,
            place=place,
            start_date=parse_approximate_date(person_csv['Start Date'])
        )

        # Set the things that weren't used to match
        position.category = 'political'
        position.end_date = parse_approximate_date(person_csv['End Date'])

        # Save the new position
        position.save()

    def handle_label(self, path, **options):

        self.path = path

        # Read and process the Executive file.
        for person_row in self.read_file('executive.csv'):
            self.import_executive(person_row)

        # Read and process the Assembly file.
        for person_row in self.read_file('assembly.csv'):
            self.import_assembly(person_row)

        # Read and process the MPLs file.
        for person_row in self.read_file('mpls.csv'):
            self.import_mpls(person_row)

        # Read and process the NCOP file.
        for person_row in self.read_file('ncop.csv'):
            self.import_ncop(person_row)

        # Read and process the IEC assignments file.
        for person_row in self.read_file('iec_seat_assignment.csv'):
            self.import_iec_assignment(person_row)

        print 'Done!'

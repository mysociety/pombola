import string

import unicodecsv as csv
from django_date_extensions.fields import ApproximateDate

from django.core.management.base import NoArgsCommand
from django.utils.text import slugify

from pombola.core.models import (
    Person,
    Organisation,
    OrganisationKind,
    Place,
    PositionTitle,
)

# Pretty colours to make it easier to spot things.
HEADER = "\033[95m"
ENDC = "\033[0m"

start_date = ApproximateDate(year=2019, month=5, day=22)


class Command(NoArgsCommand):

    help = "Imports South Africa election results from CSV."

    def __init__(self, *args, **kwargs):
        super(Command, self).__init__(*args, **kwargs)
        self.organisation_assembly = Organisation.objects.get(slug="national-assembly")
        self.position_title_member = PositionTitle.objects.get(name="Member")

    def find_person(self, election_identifier):
        """ Find a person using their 2019 election identifier """
        people = Person.objects.filter(
            identifiers__scheme="elections_2019",
            identifiers__identifier=election_identifier,
        )
        if len(people) == 0:
            raise Exception(
                "No people found for identifier {}".format(election_identifier)
            )
        elif len(people) > 1:
            raise Exception(
                "Multiple people found for identifier {}".format(election_identifier)
            )
        else:
            return people[0]

    def match_organisation(self, name, kind):
        """ Find an organisation by name, or create one. """

        slug = slugify(name)

        kind = OrganisationKind.objects.get(slug=kind)
        return Organisation.objects.get(slug=slug, kind=kind)

    def match_place(self, name):
        """ Match up a place with its database entry, or create a new one. """

        slug = slugify(name)

        return Place.objects.get(slug=slug)

    def read_file(self, file):
        """ Iterate over a file and pass the lines to a function. """

        print HEADER + "Importing from " + file + ENDC

        with open(file) as f:
            data = csv.DictReader(f)

            for person_csv in data:
                yield person_csv

    def import_assembly(self, person_csv):
        """ Import data for the National Assembly """
        person = self.find_person(person_csv["ID"])

        # Find the place, assuming it is set
        list_name = person_csv["List"]
        if list_name != "National":
            place_name = string.replace(list_name, "Regional: ", "")
            place = self.match_place(place_name)
        else:
            place = None

        # Get the position if it already exists, if not create it
        position, created = person.position_set.get_or_create(
            organisation=self.organisation_assembly,
            title=self.position_title_member,
            place=place,
            start_date=start_date,
            defaults={"category": "political"},
        )

        if created:
            print "Created new position: {}".format(position)
        else:
            print "Existing position found: {}".format(position)

    def import_mpls(self, person_csv):
        """ Import data for the Provincial Legislatures """
        person = self.find_person(person_csv["ID"])

        # Find the place, assuming it is set
        place_name = string.replace(person_csv["List"], "Provincial: ", "")
        place = self.match_place(place_name)
        organisation = self.match_organisation(
            "{} Provincial Legislature".format(place_name), "provincial-legislature"
        )

        # Get the position if it already exists, if not create it
        position, created = person.position_set.get_or_create(
            organisation=organisation,
            title=self.position_title_member,
            place=place,
            start_date=start_date,
            defaults={"category": "political"},
        )

        if created:
            print "Created new position: {}".format(position)
        else:
            print "Existing position found: {}".format(position)

    def handle_noargs(self, **options):
        path = "pombola/south_africa/data/elections/2019/"

        # Read and process the Assembly file.
        for person_row in self.read_file(path + "national-seats-assigned.csv"):
            self.import_assembly(person_csv=person_row)

        # Read and process the MPL file.
        for person_row in self.read_file(path + "provincial-seats-assigned.csv"):
            self.import_mpls(person_csv=person_row)

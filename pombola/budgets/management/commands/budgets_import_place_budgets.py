import re

import unicodecsv as csv

from django.core.exceptions import ObjectDoesNotExist
from django.core.exceptions import MultipleObjectsReturned
from django.core.management.base import LabelCommand

from django.utils.text import slugify

from django_date_extensions.fields import ApproximateDate

from pombola.core.models import (
    Place, ContentType
)

from pombola.budgets.models import Budget, BudgetSession

# Pretty colours to make it easier to spot things.
HEADER = '\033[95m'
ENDC = '\033[0m'

class Command(LabelCommand):

    help = 'Imports place budgets from CSV.'

    args = '<filename budget_session organisation currency>'

    def __init__(self, *args, **kwargs):
        super(Command, self).__init__(*args, **kwargs)

        self.content_type_place = ContentType.objects.get_for_model(Place)

    def match_place(self, name):
        """ Match up a place with its database entry, or create a new one. """

        slug = slugify(name)

        place, created = Place.objects.get_or_create(slug=slug, kind_id=1)

        if created:
            place.name = name
            place.save()
            print 'Created new place ' + slug + " as " + name

        return place

    def read_file(self, file):
        """ Deal with the business of actually iterating over a file and passing the lines to a function. """

        print HEADER + 'Importing from ' + file + ENDC

        with open(file) as f:

            # Use a DictReader so this is a bit more futureproof if the CSV changes.
            data = csv.DictReader(f)

            # Iterate over the data, call the function given.
            for csv_row in data:
                yield csv_row

    def import_budget(self, row, budget_session, organisation, currency):
        """ Import a budget for a place. """

        # Find the place
        place = self.match_place(row['Place Name'].strip())

        # Get the position if it already exists, if not create it
        budget = Budget.objects.create(
            content_type=self.content_type_place,
            object_id=place.id,
            budget_session=budget_session,
            organisation=organisation,
            name=row['Budget Name'],
            value=row['Budget Value'],
            currency=currency,
        )

    def handle(self, filename, budget_session, organisation, currency, *args, **options):

        budget_session_object = BudgetSession.objects.get(id=int(budget_session))

        # Read and process the file.
        for row in self.read_file(filename):
            self.import_budget(row, budget_session_object, organisation, currency)

        print 'Done!'

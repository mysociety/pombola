# This is a very simple script to import basic CSV with the following columns:
#
#   person_name
#   position_title
#   place_kind
#   place_name
#   organisation_kind
#   organisation_name
#
# The various person etc entries will be created if needed (ie if there is no
# exact match).
#
# GOTCHAS
#
#   * If the organisation or place already exist the associated place_kind will
#     not be used, but will be created.
#
# TODO
#
#   * Add tests


import csv

from django.core.management.base import LabelCommand

from django.utils.text import slugify

from pombola.core.models import (
    Organisation,
    OrganisationKind,
    Person,
    Place,
    PlaceKind,
    Position,
    PositionTitle,
    )


def get_or_create(model, name, field="name", defaults={}):

    if not name:
        return None

    defaults['slug'] = slugify(name)

    kwargs = {
        field: name
    }

    (obj, created) = model.objects.get_or_create(defaults=defaults, **kwargs)

    return obj


class Command(LabelCommand):
    help = 'Import positions from a very basic CSV format'
    args = '<positions CSV file>'

    # option_list = LabelCommand.option_list + (
    #     make_option('--commit', action='store_true', dest='commit', help='Actually update the database'),
    # )

    def handle_label(self,  input_filename, **options):

        csv_file = csv.DictReader(open(input_filename, 'rb'))

        for line in csv_file:

            person = get_or_create(Person, line['person_name'], field="legal_name")

            organisation_kind = get_or_create(OrganisationKind, line['organisation_kind'])
            organisation      = get_or_create(Organisation,     line['organisation_name'], defaults={ "kind": organisation_kind })

            place_kind = get_or_create(PlaceKind, line['place_kind'])
            place      = get_or_create(Place,     line['place_name'], defaults={"kind": place_kind})

            position_title = get_or_create(PositionTitle, line['position_title'])

            # Now create the position
            Position.objects.get_or_create(
                person = person,
                place = place,
                organisation = organisation,
                title = position_title,
                category = "political",
            )

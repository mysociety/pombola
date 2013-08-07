#!/usr/bin/env python

# This script requires the CSV version of
# "/home/mark/Dropbox/Mzalendo/Final Constituencies and Wards Description.pdf"
# (in Dropbox) which contains details of every ward of every
# constituency, and will create Place objects for each ward, with the
# appropriate parent constituency, in Mzalendo. Note that it doesn't
# create areas in MapIt, although this might be desirable.

import csv, re, sys
from pombola.core.models import Place, PlaceKind, ParliamentarySession
from django.core.management.base import LabelCommand
from django.template.defaultfilters import slugify
from optparse import make_option

class Command(LabelCommand):
    help = 'Add the wards for the 2013 election as Places in Mzalendo, with the right parent constituency'
    args = '<Final Constituencies and Wards Description CSV file>'

    option_list = LabelCommand.option_list + (
        make_option('--commit', action='store_true', dest='commit', help='Actually update the database'),
        )

    def handle_label(self,  input_filename, **options):

        next_session = ParliamentarySession.objects.get(slug='na2013')

        # Get (or create) the PlaceKind for wards:

        try:
            ward_place_kind = PlaceKind.objects.get(slug='ward')
        except PlaceKind.DoesNotExist:
            ward_place_kind = PlaceKind(slug="ward",
                                         name="Ward",
                                         plural_name="Wards")
            name = str(ward_place_kind).encode('utf-8')
            if options['commit']:
                print >> sys.stderr, "Saving", name
                ward_place_kind.save()
            else:
                print >> sys.stderr, "Not saving", name, "because --commit wasn't specified"

        with open(input_filename) as fp:

            reader = csv.reader(fp)
            for row in reader:
                # The column headings change at various points in the
                # file, so save them when they appear:
                if re.search('County No', row[0]):
                    headings = [c.strip() for c in row]
                else:
                    # Otherwise create a dictionary that maps headings
                    # to column values:
                    row_dict = dict(zip(headings, (c.strip() for c in row)))
                    if row_dict['County Name'] or row_dict['Constituency Name']:
                        # If County Name or Constituency Name is
                        # present, this introduces a new county +
                        # constituency:
                        county_name = row_dict['County Name']
                        current_county_number = int(row_dict['County No.']) if re.search('^\d+$', c) else None
                        current_county_name = row_dict['County Name']
                        # There are a couple of special cases where
                        # the county name is in the wrong column:
                        if row_dict['Constituency Name'] == 'Isiolo North':
                            current_county_name = 'Isiolo'
                        elif row_dict['Constituency Name'] == 'Luanda':
                            current_county_name = 'Vihiga'
                            current_county_number = 38
                        current_constituency_name = row_dict['Constituency Name']
                        constituency_number_column = headings.index('Constituency No.') + 1
                        current_constituency_number = int(row[constituency_number_column])

                    else:
                        # Otherwise this is a row that gives details
                        # of the ward:
                        ward_number = row_dict['County Assembly Ward No.']
                        ward_name = row_dict['County Assembly Ward Name']

                        # The final line of the file has no ward
                        # details, so skip any such line:
                        if not ward_name:
                            continue

                        # print current_county_number, current_county_name, current_constituency_number, current_constituency_name, ward_number, ward_name

                        # The first of these seems likely to be a
                        # mistake, but we do this to match the
                        # constituency correctly:
                        fixes = {'Ol Joro Orok': 'Ol Jorok',
                                 'Mukurweni': 'Mukurweini',
                                 'Dagoreti North': 'Dagoretti North'}

                        fixed_constituency_name = fixes.get(current_constituency_name,
                                                            current_constituency_name)

                        constituency_slug = slugify(fixed_constituency_name) + '-2013'

                        constituency = Place.objects.get(kind__name='Constituency',
                                                         parliamentary_session=next_session,
                                                         slug=constituency_slug)

                        ward_slug = 'ward-' + slugify(ward_name)

                        try:
                            ward_place = Place.objects.get(slug=ward_slug)
                        except Place.DoesNotExist:
                            ward_place = Place(slug=ward_slug,
                                               name=ward_name.decode('utf-8'),
                                               kind=ward_place_kind,
                                               parent_place=constituency,
                                               parliamentary_session=next_session)
                        if options['commit']:
                            print >> sys.stderr, "Saving", ward_place
                            ward_place.save()
                        else:
                            print >> sys.stderr, "Not saving", ward_place, "because --commit wasn't specified"

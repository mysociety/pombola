from collections import defaultdict
import csv
from dateutil import parser
from optparse import make_option
import re
import sys

from django.core.management.base import BaseCommand, CommandError

from pombola.hansard.models import Entry, Venue

class Command(BaseCommand):
    """Output statistics on speeches from Hansard for a date range"""

    option_list = BaseCommand.option_list + (
        make_option(
            '--date-from',
            dest='date_from',
            help='The start date for the statistics'),
        make_option(
            '--date-to',
            dest='date_to',
            help='The end date for the statistics'),)

    help = 'Output statistics on speeches from Hansard for a date range'

    def handle(self, **options):
        if not options['date_from']:
            raise CommandError("You must specify --date-from")
        if not options['date_to']:
            raise CommandError("You must specify --date-to")
        date_from = parser.parse(options['date_from']).date()
        date_to = parser.parse(options['date_to']).date()

        for venue in Venue.objects.all():

            vslug = venue.slug

            all_speaker_entries = Entry.objects. \
                filter(sitting__start_date__gte=date_from,
                       sitting__start_date__lte=date_to,
                       sitting__venue__slug=vslug,
                       speaker__isnull=False). \
                select_related('speaker', 'sitting'). \
                prefetch_related('speaker__position_set'). \
                prefetch_related('speaker__position_set__title'). \
                prefetch_related('speaker__position_set__place')

            # The gender split is easy to find, so do that first:

            gender_counts = {
                'Male': all_speaker_entries.filter(speaker__gender='m').count(),
                'Female': all_speaker_entries.filter(speaker__gender='f').count(),
                'Unknown': all_speaker_entries.filter(speaker__gender='').count()
            }

            self.write_csv(vslug + '-gender.csv', gender_counts)

            # These dictionaries are for storing the position-based results:
            county_associated = defaultdict(int)
            party_counts = defaultdict(int)
            coalition_counts = defaultdict(int)

            for e in all_speaker_entries:
                sitting_date = e.sitting.start_date
                speaker = e.speaker
                positions = speaker.position_set.all(). \
                    current_politician_positions(sitting_date)

                # Find positions associated with counties:

                county_associated_positions = []

                for p in positions.filter(
                    title__name__in=('Senator', 'Governor'),
                    place__kind__name='County'):
                    county_associated_positions.append((p.title.name, p.place.name))

                for p in positions.filter(
                    title__name='Member of the National Assembly',
                    place__kind__name='Constituency',
                    place__parent_place__kind__name='County'):
                    county_associated_positions.append((p.title.name, p.place.parent_place.name))

                for p in positions.filter(
                    title__name='Member of the National Assembly',
                    # The spelling of the subtitle 'Women's representative' varies:
                    subtitle__regex="omen.*epresentative",
                    place__kind__name='County'):
                    county_associated_positions.append((p.title.name, p.place.name))

                if len(county_associated_positions) > 1:
                    raise Exception, "Warning: found multiple county-associated positions for {0}: {1}".format(
                        speaker,
                        county_associated_positions)
                if len(county_associated_positions) == 1:
                    county_associated[county_associated_positions[0]] += 1

                # Now find party and coalition memberships:

                party_memberships = positions. \
                    filter(title__name='Member'). \
                    filter(organisation__kind__name='Political Party')
                coalition_memberships = positions. \
                    filter(title__name='Coalition Member'). \
                    filter(organisation__kind__name='Coalition')

                for mtype, counts, memberships in (
                        ("party", party_counts, party_memberships),
                        ("coalition", coalition_counts, coalition_memberships)):

                    count = memberships.count()

                    if count > 1:
                        print >> sys.stderr, "Multiple {0} memberships found for {1}: {2}".format(
                            mtype, speaker, memberships)
                    elif count == 1:
                        name = memberships[0].organisation.name
                        counts[name] += 1
                    else:
                        counts['Unknown'] += 1

            # Write out those results:

            self.write_csv(vslug + '-party_counts.csv', party_counts)
            self.write_csv(vslug + '-coalition_counts.csv', coalition_counts)

            with open(vslug + '-county-associated.csv', 'w') as fp:
                writer = csv.writer(fp)
                for t, v in county_associated.items():
                    writer.writerow([t[0], t[1], str(v)])

    def write_csv(self, filename, dictionary):
        with open(filename, 'w') as fp:
            writer = csv.writer(fp)
            for k, v in sorted(dictionary.items()):
                writer.writerow([k, str(v)])

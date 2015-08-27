from collections import defaultdict
import csv
from dateutil import parser
from optparse import make_option

from django.core.management.base import BaseCommand, CommandError
from django.db.models import Count

from pombola.core.models import PopoloPerson
from pombola.hansard.models import Entry, Venue

class MultipleMembershipsException(Exception):
    pass

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

    def position_data(self, speaker, date, cached_position_data):

        cache_key = (speaker, date)
        if cache_key in cached_position_data:
            return cached_position_data[cache_key]

        results = {
            'county_associated': [],
            'party_membership': [],
            'coalition_membership': []
        }

        positions = speaker.position_set.all(). \
            current_politician_positions(date)

        # Find positions associated with counties:

        for p in positions.filter(
            title__name__in=('Senator', 'Governor'),
            place__kind__name='County'):
            results['county_associated'].append((p.title.name, p.place.name))

        for p in positions.filter(
            title__name='Member of the National Assembly',
            place__kind__name='Constituency',
            place__parent_place__kind__name='County'):
            results['county_associated'].append((p.title.name, p.place.parent_place.name))

        for p in positions.filter(
            title__name='Member of the National Assembly',
            # The spelling of the subtitle 'Women's representative' varies:
            subtitle__regex="omen.*epresentative",
            place__kind__name='County'):
            results['county_associated'].append((p.title.name, p.place.name))

        # Now find party and coalition memberships:

        party_memberships = positions. \
            filter(title__name='Member'). \
            filter(organisation__kind__name='Political Party')
        coalition_memberships = positions. \
            filter(title__name='Coalition Member'). \
            filter(organisation__kind__name='Coalition')

        for mtype, memberships in (
                ("party", party_memberships),
                ("coalition", coalition_memberships)):

            for m in memberships:
                results[mtype + '_membership'].append(m.organisation.name)

        for k, v in results.items():
            count = len(v)
            if count > 1:
                fmt = "Multiple {0} memberships found for {1}: {2}"
                message = fmt.format(k, speaker, v)
                raise MultipleMembershipsException, message
            elif count == 1:
                results[k] = v[0]
            else:
                results[k] = ('', '') if k == 'county_associated' else ''

        cached_position_data[cache_key] = results

        return results


    def handle(self, **options):
        position_data_cache = {}

        if not options['date_from']:
            raise CommandError("You must specify --date-from")
        if not options['date_to']:
            raise CommandError("You must specify --date-to")
        date_from = parser.parse(options['date_from']).date()
        date_to = parser.parse(options['date_to']).date()

        date_difference = date_to - date_from
        date_midpoint = date_from + (date_difference / 2)

        print "Generating all-speakers.csv"

        with open('all-speakers.csv', 'w') as fp:
            writer = csv.writer(fp)
            writer.writerow(['Name',
                             'Gender',
                             'Position',
                             'County',
                             'Party',
                             'Coalition',
                             'Appearances'])

            for d in Entry.objects. \
                filter(sitting__start_date__gte=date_from,
                       sitting__start_date__lte=date_to,
                       speaker__isnull=False). \
                values('speaker'). \
                annotate(Count('speaker')). \
                order_by('speaker'):
                speaker = Person.objects.get(pk=d['speaker'])
                speeches = d['speaker__count']

                print "speaker:", speaker, "speeches:", speeches

                # Look for political positions occupied mid-way through
                # the date range:

                position_results = self.position_data(speaker, date_midpoint, position_data_cache)

                writer.writerow([speaker.legal_name,
                                 speaker.gender,
                                 position_results['county_associated'][0],
                                 position_results['county_associated'][1],
                                 position_results['party_membership'],
                                 position_results['coalition_membership'],
                                 speeches])

        for venue in Venue.objects.all():

            vslug = venue.slug

            print "Generating data for " + vslug

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

            print "  Writing gender data for " + vslug

            gender_counts = {
                'Male': all_speaker_entries.filter(speaker__gender='male').count(),
                'Female': all_speaker_entries.filter(speaker__gender='female').count(),
                'Unknown': all_speaker_entries.filter(speaker__gender='').count()
            }

            self.write_csv(vslug + '-gender.csv', gender_counts)

            print "  Writing county, party and coalition data for " + vslug

            # These dictionaries are for storing the position-based results:
            county_associated = defaultdict(int)
            party_counts = defaultdict(int)
            coalition_counts = defaultdict(int)

            for e in all_speaker_entries:
                sitting_date = e.sitting.start_date
                speaker = e.speaker
                positions = self.position_data(speaker, sitting_date, position_data_cache)
                party_counts[positions['party_membership']] += 1
                coalition_counts[positions['coalition_membership']] += 1
                county_associated[positions['county_associated']] += 1

            # Write out those results:

            self.write_csv(vslug + '-party_counts.csv', party_counts)
            self.write_csv(vslug + '-coalition_counts.csv', coalition_counts)

            with open(vslug + '-county-associated.csv', 'w') as fp:
                writer = csv.writer(fp)
                for t, v in county_associated.items():
                    writer.writerow([t[0], t[1], str(v)])

            if vslug == 'national_assembly':

                print "  Writing women representative data"

                with open(vslug + '-women-representatives.csv', 'w') as fp:
                    writer = csv.writer(fp)
                    writer.writerow(['Name',
                                     'Gender',
                                     'Position',
                                     'County',
                                     'Party',
                                     'Coalition',
                                     'Appearances'])

                    all_women_representative_speaker_entries = \
                        all_speaker_entries.filter(
                            speaker__position__title__name='Member of the National Assembly',
                            speaker__position__subtitle__regex="omen.*epresentative",
                        )

                    for d in all_women_representative_speaker_entries. \
                        values('speaker'). \
                        annotate(Count('speaker')). \
                        order_by('speaker'):
                        speaker = Person.objects.get(pk=d['speaker'])
                        speeches = d['speaker__count']

                        position_results = self.position_data(speaker, date_midpoint, position_data_cache)

                        writer.writerow([speaker.legal_name,
                                         speaker.gender,
                                         position_results['county_associated'][0],
                                         position_results['county_associated'][1],
                                         position_results['party_membership'],
                                         position_results['coalition_membership'],
                                         speeches])

    def write_csv(self, filename, dictionary):
        with open(filename, 'w') as fp:
            writer = csv.writer(fp)
            for k, v in sorted(dictionary.items()):
                writer.writerow([k, str(v)])

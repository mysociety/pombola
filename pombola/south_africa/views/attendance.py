from __future__ import division

import dateutil
import json
import requests
import datetime
from urlparse import urlsplit

from .constants import API_REQUESTS_TIMEOUT

from django.core.cache import caches
from django.views.generic import TemplateView
from django.db.models import Q

from pombola.core.models import Position


class SAMpAttendanceView(TemplateView):
    template_name = "south_africa/mp_attendance.html"

    def calculate_abs_percenatge(self, num, total):
        """
        Return the truncated value of num, as a percentage of total.
        """
        return int("{:.0f}".format(num / total * 100))

    def download_attendance_data(self):
        attendance_url = next_url = 'https://api.pmg.org.za/committee-meeting-attendance/summary/'

        cache = caches['pmg_api']
        results = cache.get(attendance_url)

        if results is None:
            results = []
            while next_url:
                resp = requests.get(next_url, timeout=API_REQUESTS_TIMEOUT)
                data = json.loads(resp.text)
                results.extend(data.get('results'))

                next_url = data.get('next')

            cache.set(attendance_url, results)

        # Results are returned from the API most recent first, which
        # is convenient for us.
        return results

    def just_path_of_pa_url(self, ma):
        return dict(
            ma, member=dict(
                ma['member'], pa_url=urlsplit(ma['member']['pa_url']).path))

    def filter_attendance(self, annual_attendance, party, position):
        """
        Filter meeting attendance to only include items which match
        the party and position selections by the user.
        """

        attendance_summary = annual_attendance['attendance_summary']
        if party:
            attendance_summary = [ma for ma in attendance_summary if
                ma['member']['party_name'] == party]

        year_end_date = datetime.datetime.strptime(
            annual_attendance['end_date'], "%Y-%m-%d").date()
        today = datetime.date.today()

        active_minister_positions = Position.objects.filter(
                Q(title__slug__startswith='minister') |
                Q(title__slug__startswith='deputy-minister')
            ).currently_active(
                today if year_end_date > today else year_end_date).select_related('person')

        active_minister_slugs = set(am.person.slug for am in active_minister_positions)

        minister_attendance = []
        for attendance in attendance_summary:
            if attendance['member']['pa_url']:
                slug = attendance['member']['pa_url'].split('/')[-2]
                if slug in active_minister_slugs:
                    minister_attendance.append(attendance)
                    attendance_summary.remove(attendance)
                    active_minister_slugs.remove(slug)

        if position == 'ministers':
            # Some Ministers don't have attendance records,
            # and we need to show that they haven't attendended any meetings
            for position in active_minister_positions:
                minister = position.person
                if minister.slug in active_minister_slugs:

                    # Build name consistent with PMG data
                    initials = "".join(name[0].upper() for name in minister.given_name.split())
                    minister_name = "{}, {} {}".format(
                        minister.family_name, minister.title, initials)

                    minister_attendance.append({
                        'member': {
                            'name': minister_name,
                            'pa_url': minister.get_absolute_url(),
                            'party_name': minister.parties()[0].slug.upper()},
                        'attendance': {
                            'P': 0}
                    })
            attendance = minister_attendance

        else:
            # Show Members returned who we aren't considered Ministers
            # Exclude records without a pa_url,
            # as we don't know whether it's an MP or Minister
            attendance = [
                self.just_path_of_pa_url(ma)
                for ma in attendance_summary if ma['member']['pa_url']]

        return attendance

    def get_context_data(self, **kwargs):
        data = self.download_attendance_data()

        #  A:   Absent
        #  AP:  Absent with Apologies
        #  DE:  Departed Early
        #  L:   Arrived Late
        #  LDE: Arrived Late and Departed Early
        #  P:   Present

        present_codes = ['P', 'L', 'LDE', 'DE']
        arrive_late_codes = ['L', 'LDE']
        depart_early_codes = ['DE', 'LDE']

        context = {}
        context['year'] = str(
            dateutil.parser.parse(data[0]['end_date']).year)
        context['party'] = ''
        context['position'] = 'ministers'

        for key in ('year', 'party', 'position'):
            if key in self.request.GET:
                context[key] = self.request.GET[key]

        context['attendance_data'] = []
        context['years'] = []
        context['download_url'] = 'http://api.pmg.org.za/committee-meeting-attendance/data.xlsx'

        for annual_attendance in data:
            year = str(dateutil.parser.parse(annual_attendance['end_date']).year)
            context['years'].append(year)

            if year == context['year']:
                parties = set(ma['member']['party_name'] for
                    ma in annual_attendance['attendance_summary'])
                parties.discard(None)
                context['parties'] = sorted(parties)


                attendance_summary = self.filter_attendance(
                    annual_attendance, context['party'], context['position'])

                if context['position'] == 'mps':
                    aggregate_total = aggregate_present = 0

                    for summary in attendance_summary:
                        total = sum(v for v in summary['attendance'].itervalues())

                        present = sum(
                            v for k, v in summary['attendance'].iteritems()
                            if k in present_codes)

                        arrive_late = sum(
                            v for k, v in summary['attendance'].iteritems()
                            if k in arrive_late_codes)

                        depart_early = sum(
                            v for k, v in summary['attendance'].iteritems()
                            if k in depart_early_codes)

                        aggregate_total += total
                        aggregate_present += present

                        present_perc = self.calculate_abs_percenatge(present, total)
                        arrive_late_perc = self.calculate_abs_percenatge(arrive_late, total)
                        depart_early_perc = self.calculate_abs_percenatge(depart_early, total)

                        context['attendance_data'].append({
                            "name": summary['member']['name'],
                            "pa_url": summary['member']['pa_url'],
                            "party_name": summary['member']['party_name'],
                            "present": present_perc,
                            "absent": 100 - present_perc,
                            "arrive_late": arrive_late_perc,
                            "depart_early": depart_early_perc,
                            "total": total,
                        })

                    if aggregate_total == 0:
                        # To avoid a division by zero if there's no data...
                        aggregate_attendance = -1
                    else:
                        aggregate_attendance = self.calculate_abs_percenatge(aggregate_present, aggregate_total)
                    context['aggregate_attendance'] = aggregate_attendance

                else:
                    for summary in attendance_summary:
                        present = sum(
                            v for k, v in summary['attendance'].iteritems()
                            if k in present_codes)
                        context['attendance_data'].append({
                                "name": summary['member']['name'],
                                "pa_url": summary['member']['pa_url'],
                                "party_name": summary['member']['party_name'],
                                "present": present,
                        })

        return context

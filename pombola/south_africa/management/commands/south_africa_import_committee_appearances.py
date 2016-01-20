from datetime import datetime
from optparse import make_option
import os
from os.path import exists

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from instances.models import Instance

from za_hansard.importers.import_json import ImportJson
from za_hansard.models import PMGCommitteeReport


def person_accept_check(popit_person, date):
    """Check that the popit_person was a member of the NA on date.

    We only want to associate committee appearances with people who
    were members of the National Assembly on the date of the meeting
    in question.
    """
    from pombola.core.models import Position

    person_id = int(popit_person.popit_id.rsplit(':', 1)[1])

    qs = (Position.objects
          .filter(
              person__id=person_id,
              title__slug='member',
              organisation__slug='national-assembly',
              )
          .currently_active(date)
          )

    return qs.exists()


class Command(BaseCommand):
    help = 'Import NA committee appearances scraped by ZA hansard.'

    option_list = BaseCommand.option_list + (
        make_option(
            '--commit',
            default=False,
            action='store_true',
            help='Actually make changes to the database',
        ),
        make_option(
            '--sayit-instance',
            type='str',
            default='default',
            help='SayIt instance to import into',
        ),
        make_option(
            '--delete-existing',
            default=False,
            action='store_true',
            help='Delete existing SayIt speeches (with --import-to-sayit)',
        ),
        make_option(
            '--committee',
            type='int',
            help='Only process the committee with this ID',
        ),
        make_option(
            '--meeting',
            type='int',
            help='Only process the meeting with this ID',
        ),
    )

    @property
    def process_all_committees(self):
        return self.options['committee'] is None

    @property
    def process_all_meetings(self):
        return self.options['meeting'] is None

    def specified_committee(self, committee_id):
        if committee_id is not None:
            return self.options['committee'] == int(committee_id)

    def specified_meeting(self, meeting_id):
        if meeting_id is not None:
            return self.options['meeting'] == int(meeting_id)

    def should_process_report(self, pcr):
        if not (self.process_all_committees or
                self.specified_committee(pcr.api_committee_id)):
            return False
        if not (self.process_all_meetings or
                self.specified_meeting(pcr.api_meeting_id)):
            return False
        return True

    def handle(self, *args, **options):
        self.options = options

        try:
            sayit_instance = Instance.objects.get(
                label=options['sayit_instance']
            )
        except Instance.DoesNotExist:
            raise CommandError(
                "SayIt instance (%s) not found".format(
                    options['sayit_instance']
                    )
                )

        reports = reports_all = PMGCommitteeReport.objects.all()
        section_ids = []

        if not options['delete_existing']:
            reports = reports_all.filter(sayit_section=None)

        for report in reports.iterator():

            if not self.should_process_report(report):
                continue

            filename = os.path.join(
                settings.COMMITTEE_CACHE,
                '{0}.json'.format(report.id)
            )
            if not exists(filename):
                message = "WARNING: couldn't find a JSON file for report with ID {0}\n"
                self.stdout.write(message.format(report.id))
                continue

            importer = ImportJson(
                instance=sayit_instance,
                delete_existing=options['delete_existing'],
                popit_url='http://za-new-import.popit.mysociety.org/api/v0.1/',
                commit=options['commit'],
                popit_id_blacklist=(
                    'core_person:3739',
                    'core_person:4555',
                    'core_person:5421',
                    'core_person:8277',
                    ),
                person_accept_check=person_accept_check,
            )
            try:
                message = "Importing {0} ({1})\n"
                self.stdout.write(message.format(report.id, filename))
                section = importer.import_document(filename)

                report.sayit_section = section
                report.last_sayit_import = datetime.now().date()
                if options['commit']:
                    report.save()

                section_ids.append(section.id)

            except Exception as e:
                message = 'WARNING: failed to import {0}: {1}'
                self.stderr.write(message.format(report.id, e))

        self.stdout.write(str(section_ids))
        self.stdout.write('\n')

        self.stdout.write(
            'Imported {0} / {1} sections\n'.format(
                len(section_ids),
                len(reports_all)
            )
        )

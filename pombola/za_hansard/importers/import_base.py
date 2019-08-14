import logging

from django.core.exceptions import ObjectDoesNotExist

from popolo_name_resolver.resolve import ResolvePopoloName
from speeches.models import Speaker

logger = logging.getLogger(__name__)


class AllowedPersonFilter(object):

    def __init__(self, pombola_id_blacklist):
        self.pombola_id_blacklist = set(pombola_id_blacklist or ())

    def is_person_allowed(self, person):
        try:
            pombola_person = person.speaker.pombola_link.pombola_person
        except ObjectDoesNotExist:
            # If there's no corresponding Pombola person, allow the
            # speaker anyway - there may be an existing
            # non-Pombola-associated person for this name.
            return True
        pombola_person_id = pombola_person.id
        return pombola_person_id not in self.pombola_id_blacklist


class ImportZAMixin(object):
    def __init__(self, instance=None, commit=True, pombola_id_blacklist=None, **kwargs):
        super(ImportZAMixin, self).__init__(
            instance=instance,
            commit=commit,
            **kwargs
        )
        self.person_cache = {}
        self.pombola_id_blacklist = pombola_id_blacklist

    def set_resolver_for_date(self, date_string='', date=None):
        self.resolver = ResolvePopoloName(
            date=date,
            date_string=date_string,
            person_filter=AllowedPersonFilter(self.pombola_id_blacklist),
        )

    def debug_output_csv_row(self, pombola_person_slug, from_cache, our_speaker, speaker_from_slug):
        '''A method to help produce data for analyzing name resolution results'''
        import csv
        with open('name-resolution.log', 'ab') as f:
            writer = csv.writer(f)
            writer.writerow([
                str(self.resolver.date),
                '' if pombola_person_slug is None else pombola_person_slug,
                our_speaker.id if our_speaker else '',
                our_speaker.name.encode('utf-8') if our_speaker else '',
                speaker_from_slug.id if speaker_from_slug else '',
                speaker_from_slug.name.encode('utf-8') if speaker_from_slug else '',
            ])

    def get_person(self, name, party, pombola_person_slug=None):

        # If we can directly find the person from the
        # pombola_person_slug, use that - the Code4SA / PMG
        # identification of speakers seems to be better than that from
        # popolo_name_resolver.
        speaker_from_slug = None
        if pombola_person_slug is not None:
            speaker_from_slug = Speaker.objects.filter(
                identifiers__scheme='pombola_person_slug',
                identifiers__identifier=pombola_person_slug).first()
            if speaker_from_slug:
                return speaker_from_slug

        cached = self.person_cache.get(name, None)
        if cached:
            return cached

        display_name = name or '(narrative)'

        speaker = None
        person = None

        if name:
            person = self.resolver.get_person(display_name, party)
            if person:
                speaker = person.speaker

        if not speaker:
            try:
                speaker = Speaker.objects.get(instance=self.instance, name=display_name)
            except Speaker.DoesNotExist:
                speaker = Speaker(instance=self.instance, name=display_name)
                if self.commit:
                    speaker.save()

        self.person_cache[name] = speaker
        return speaker

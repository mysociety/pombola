from collections import Counter
import re
import sys

from django.conf import settings
from django.core.management.base import BaseCommand

from popit.models import Person as PopItPerson

from pombola.core.models import Person, Identifier

from speeches.models import Speaker, Speech

# We've ended up in a situation where there are lots of Person objects
# from popit-django that refer to old PopIt URLs still in the database
# - even worse, they may still be referenced by SayIt Speaker
# objects. This script should safely get rid of these without breaking
# any references from Speaker objects.

current_popit_api_base_url = settings.POPIT_API_URL

# This is the format of the URLs currently in PopIt:

current_popit_id_re = re.compile(
    r'^{0}persons/core_person:(?P<pombola_id>\d+)$'.format(
        current_popit_api_base_url
    )
)

# This matches any PopIt URLs that have the Pombola Person ID embedded
# in them.

other_popit_id_re = re.compile('za-new-import.*core_person/(?P<pombola_id>\d+)$')

# This matches the older form of PopIt URL, which had a
# pombola.core.models.Identifer encoded instead of a Pombola Person ID
# directly embedded in the URL.

identifier_based_re = re.compile(
    r'http://za-peoples-assembly.popit.mysociety.org/api/v0.1/' +
    r'persons/org.mysociety.za(?P<pombola_identifier>.*)$'
)

def get_popit_url_info(popit_url):
    """Return all the information that we can derive from a PopIt URL

    This returns a dict, with key / value pairs representing whether
    this is a current PopIt URL (i.e. matches the format currently in
    use), a Pombola Person object ID (if one could be derived from the
    URL) or whether it's "impossible" to deal with - we couldn't parse
    it or it referred to a non-existent person or identifier."""

    m_current = current_popit_id_re.search(popit_url)
    m_other_popit = other_popit_id_re.search(popit_url)
    m_old_identifier = identifier_based_re.search(popit_url)

    result = {
        'impossible': False,
        'current': False,
        'pombola_id': None,
    }

    m_either = m_current or m_other_popit
    if m_either:
        pombola_id = int(m_either.group('pombola_id'))
        result['pombola_id'] = pombola_id
        result['current'] = bool(m_current)
        try:
            Person.objects.get(pk=pombola_id)
        except Person.DoesNotExist:
            message = "Warning: no Pombola Person corresponding to {0}"
            print message.format(popit_url)
            result['impossible'] = True
    elif m_old_identifier:
        # Also look out for older URLs that are based on an
        # identifier object with scheme org.mysociety.za:
        try:
            identifier = Identifier.objects.get(
                scheme='org.mysociety.za',
                identifier=m_old_identifier.group('pombola_identifier')
            )
            pombola_person = identifier.content_object
            if pombola_person:
                result['pombola_id'] = pombola_person.id
            else:
                print "Warning: {0} had no content_object set".format(
                    identifier
                )
                result['impossible'] = True
        except Identifier.DoesNotExist:
            message = "Warning, no Pombola Person corresponding to {0}"
            print message.format(popit_url)
            result['impossible'] = True
    else:
        print "Warning: no case would handle {0}".format(popit_url)
        result['impossible'] = True

    return result

def safely_delete(p):
    # Since the django-sayit Speaker references the PopIt Person with
    # on_delete=models.PROTECT, we have to delete any speaker that
    # refers to it first; also double-check that there are no speeches
    # still associated with that speaker before doing that. In
    # addition, there may be EntityName objects still referring to
    # them, which also use PROTECT, so delete any of them too.
    all_deleted = True
    for s in p.speaker_set.all():
        if s.speech_set.count() == 0:
            s.delete()
        else:
            message = "!!! Couldn't delete; there were still {0} speeches associated with {1} {2}"
            all_deleted = False
            print message.format(s.speech_set.count(), s.id, s)
    for en in p.entityname_set.all():
        en.delete()
    if all_deleted:
        p.delete()

def check_for_duplicate_urls():
    # Check that there are no duplicate popit_url entries:
    popit_url_counter = Counter()
    for p in PopItPerson.objects.all():
        popit_url_counter[p.popit_url] += 1
    duplicate_urls_found = False
    for popit_url, count in popit_url_counter.items():
        if count > 1:
            print "There were multiple entries for " + popit_url
            duplicate_urls_found = True
    if duplicate_urls_found:
        sys.exit(1)


class Command(BaseCommand):

    def handle(*args, **options):

        check_for_duplicate_urls()

        popit_url_to_pk = {p.popit_url: p.id for p in PopItPerson.objects.all()}

        # Build up some preliminary mappings:

        popit_url_to_pombola_id = {}
        pombola_id_to_current_popit_url = {}
        popit_url_to_details = {}

        impossible_ids = set()

        for popit_url, pk in popit_url_to_pk.items():
            details = get_popit_url_info(popit_url)
            popit_url_to_details[popit_url] = details
            pombola_id = details['pombola_id']
            if details['impossible']:
                impossible_ids.add(pk)
            elif pombola_id:
                popit_url_to_pombola_id[popit_url] = pombola_id
                if details['current']:
                    pombola_id_to_current_popit_url[pombola_id] = popit_url

        # Now build a mapping from the id of each row of the
        # popit_person table that should be deleted to the id of its
        # replacement.

        mapping_from_deleted = {}

        for popit_url, pk in popit_url_to_pk.items():
            details = popit_url_to_details[popit_url]
            if details['impossible']:
                continue
            # The rows with canonical URLs won't be rewritten:
            if details['current']:
                continue
            # Ignore any row where we couldn't find the Pombola Person
            # that it refers to:
            pombola_id = details['pombola_id']
            if not pombola_id:
                continue
            # Otherwise we should be able to delete these rows after
            # replacing any references to them.
            current_popit_url = pombola_id_to_current_popit_url[pombola_id]
            mapping_from_deleted[pk] = popit_url_to_pk[current_popit_url]

        # Now replace all the references in the speeches_speaker table:

        for speaker in Speaker.objects.all():
            if not speaker.person:
                continue
            popit_person_id = speaker.person.id
            new_popit_person_id = mapping_from_deleted.get(popit_person_id)
            if not new_popit_person_id:
                continue
            new_popit_person = PopItPerson.objects.get(pk=new_popit_person_id)
            print "Replacing {0} with {1}".format(
                speaker.person, new_popit_person
            )
            # There might already be a Speaker that points to the new
            # popit-django Person; if there is, then use that instead,
            # otherwise modify the speaker to point to the new person.
            try:
                existing_speaker = Speaker.objects.get(
                    instance=speaker.instance,
                    person=new_popit_person
                )
                message = "A Speaker referring to {0} already existed..."
                message += "\n... replacing the speaker in all speeches"
                print message.format(new_popit_person)
                Speech.objects.filter(speaker=speaker). \
                    update(speaker=existing_speaker)
            except Speaker.DoesNotExist:
                speaker.person = new_popit_person
                speaker.save()

        # Now remove all the deleted PopIt Person rows and Speaker
        # rows that reference them, that we've now ensured they're
        # safe to delete.

        print "Deleting replaced PopIt Person and Speaker objects that we've replaced"
        for p in PopItPerson.objects.filter(id__in=mapping_from_deleted.keys()):
            safely_delete(p)

        # Finally, delete any rows which are "impossible" (i.e. those
        # that we could not find a corresponding Pombola Person for).

        print "Deleting any PopIt Person and Speaker objects that no longer refer to people"
        for p in PopItPerson.objects.filter(id__in=impossible_ids):
            safely_delete(p)

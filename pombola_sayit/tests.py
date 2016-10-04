from django.contrib.contenttypes.models import ContentType
from django.core.management import call_command
from django.test import TestCase

from django_date_extensions.fields import ApproximateDate

from instances.models import Instance
from pombola.core import models as pombola_models
from popolo import models as popolo_models
from slug_helpers.models import SlugRedirect
from speeches.models import Speaker

from pombola_sayit.models import PombolaSayItJoin


class SyncTests(TestCase):

    def setUp(self):
        instance = Instance.objects.create(label='default')
        # ------------------------------------------------------
        self.person_only_pombola = \
            pombola_models.Person.objects.create(
                legal_name='John Solo',
                slug='john-solo',
            )
        SlugRedirect.objects.create(
            content_type=ContentType.objects.get(
                app_label='core', model='person'),
            new_object=self.person_only_pombola,
            old_object_slug='john---solo')
        self.person_only_pombola.alternative_names.create(
            alternative_name='Han Solo',
            start_date=ApproximateDate(1977, 12, 27),
            end_date=ApproximateDate(future=True),
        )
        party_kind = pombola_models.OrganisationKind.objects.create(
            name='Political Party'
        )
        self.party = pombola_models.Organisation.objects.create(
            name='The Official Monster Raving Loony Party',
            kind=party_kind,
        )
        pombola_models.Position.objects.create(
            person=self.person_only_pombola,
            organisation=self.party,
            start_date=ApproximateDate(1990),
            end_date=ApproximateDate(1999, 12, 31),
        )
        pombola_models.Position.objects.create(
            person=self.person_only_pombola,
            organisation=self.party,
            start_date=ApproximateDate(2000, 1),
            end_date=ApproximateDate(future=True),
        )
        # ------------------------------------------------------
        self.person_with_speaker = \
            pombola_models.Person.objects.create(
                legal_name='John Loquacious',
                slug='john-loquacious',
            )
        speaker = Speaker.objects.create(
            name='John Loquacious',
            instance=instance
        )
        PombolaSayItJoin.objects.create(
            pombola_person=self.person_with_speaker,
            sayit_speaker=speaker,
        )

    def test_sync_command(self):

        sayit_speaker_id_before = \
            self.person_with_speaker.sayit_link.sayit_speaker.id
        pombola_person_ids_before = \
            set(pombola_models.Person.objects.all() \
                .values_list('id', flat=True))

        call_command('pombola_sayit_sync_pombola_to_popolo')

        speaker_ids_after = set(s.id for s in Speaker.objects.all())
        self.assertEqual(2, len(speaker_ids_after))
        self.assertIn(sayit_speaker_id_before, speaker_ids_after)
        pombola_person_ids_after = \
            set(pombola_models.Person.objects.all() \
                .values_list('id', flat=True))
        self.assertEqual(
            pombola_person_ids_before, pombola_person_ids_after
        )
        new_speaker_id = next(iter(
            speaker_ids_after - set([sayit_speaker_id_before])
        ))
        new_speaker = Speaker.objects.get(pk=new_speaker_id)
        self.assertEqual(
            new_speaker,
            self.person_only_pombola.sayit_link.sayit_speaker
        )

        memberships = popolo_models.Membership.objects.all() \
            .order_by('start_date')
        memberships = list(memberships)
        self.assertEqual(2, len(memberships))
        self.assertEqual(memberships[0].start_date, '1990-00-00')
        self.assertEqual(memberships[0].end_date, '1999-12-31')
        self.assertEqual(
            memberships[0].organization.name,
            'The Official Monster Raving Loony Party'
        )
        self.assertEqual(
            memberships[0].organization.classification,
            'Political Party'
        )
        self.assertEqual(memberships[1].start_date, '2000-01-00')
        self.assertEqual(memberships[1].end_date, None)
        self.assertEqual(
            memberships[1].organization.name,
            'The Official Monster Raving Loony Party'
        )
        self.assertEqual(
            memberships[1].organization.classification,
            'Political Party'
        )

        other_names = popolo_models.OtherName.objects.all()
        self.assertEqual(1, len(other_names))
        self.assertEqual(other_names[0].name, 'Han Solo')
        self.assertEqual(other_names[0].start_date, '1977-12-27')
        self.assertIsNone(other_names[0].end_date)

        # Check that identifiers with all slugs for that person have
        # been created.
        speaker_john_solo = Speaker.objects.get(name='John Solo')
        speaker_john_loquacious = Speaker.objects.get(name='John Loquacious')
        self.assertEqual(
            set(speaker_john_solo.identifiers.filter(
                scheme='pombola_person_slug').values_list('identifier', flat=True)),
            {'john-solo', 'john---solo'})
        self.assertEqual(
            set(speaker_john_loquacious.identifiers.filter(
                scheme='pombola_person_slug').values_list('identifier', flat=True)),
            {'john-loquacious'})

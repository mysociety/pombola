import json

from django.contrib.contenttypes.models import ContentType
from django.core.files.base import ContentFile
from django.test import TestCase

from django_date_extensions.fields import ApproximateDate

from pombola.core import models
from pombola.core.popolo import get_popolo_data
from pombola.images.models import Image

class PopoloTest(TestCase):

    def setUp(self):
        self.maxDiff = None

        self.person = models.Person.objects.create(
            legal_name='Test Person',
            slug='test-person',
            date_of_birth='1970-01-01',
        )
        self.contact_kind = models.ContactKind.objects.create(
            name="Email Address",
            slug="email",
        )
        self.email_contact = models.Contact.objects.create(
            kind = self.contact_kind,
            value = "test@example.org",
            content_type=ContentType.objects.get_for_model(models.Person),
            object_id=self.person.id,
            note='Found on the parliament website',
        )
        self.missing_email_contact = models.Contact.objects.create(
            kind = self.contact_kind,
            value = '',
            content_type=ContentType.objects.get_for_model(models.Person),
            object_id=self.person.id
        )
        self.person.add_alternative_name('Test H Person',
                                         name_to_use=True,
                                         note='Used in a newspapers')
        self.person_id = models.Identifier.objects.create(
            identifier="/person/someone",
            scheme="some.schema",
            object_id=self.person.id,
            content_type=ContentType.objects.get_for_model(models.Person))
        self.person_image = Image(
            content_object = self.person,
            source = 'Not a real image, so no source...',
        )
        self.person_image.image.save(
            name = "some-image",
            content = ContentFile(''),
        )

        self.organisation_kind = models.OrganisationKind.objects.create(
            name='Example Org Kind',
            slug='example-org-kind',
        )
        self.organisation = models.Organisation.objects.create(
            name='Test Organisation',
            slug='test-organisation',
            kind=self.organisation_kind,
            started=ApproximateDate(2009),
            ended=ApproximateDate(2011, 3, 20),
        )
        self.position_title = models.PositionTitle.objects.create(
            name="Knight of the Realm",
            slug="knight",
        )
        self.position = models.Position.objects.create(
            person=self.person,
            organisation=self.organisation,
            end_date=ApproximateDate(2013, 06),
            title=self.position_title,
        )

        self.expected_memberships = [
            {
                "end_date": "2013-06",
                "identifiers": [],
                "organization_id": "org.example/core_organisation/{organization_id}",
                "role": u"Knight of the Realm",
                "person_id": "org.example/core_person/{person_id}",
                "id": "org.example/core_position/{position_id}"
            }
        ]

        self.expected_persons = [
            {
                "contact_details": [
                    {
                        "note": u"Found on the parliament website",
                        "type": u"email",
                        "value": u"test@example.org"
                    }
                ],
                "name": u"Test Person",
                "identifiers": [
                    {
                        "scheme": u"some.schema",
                        "identifier": u"/person/someone"
                    }
                ],
                "other_names": [
                    {
                        "note": u"Used in a newspapers",
                        "name": u"Test H Person"
                    }
                ],
                "sort_name": u"Person",
                "images": [
                    {
                        "url": "http://pombola.example.org/media_root/{image_name}"
                    }
                ],
                "birth_date": "1970-01-01",
                "id": "org.example/core_person/{person_id}"
            }
        ]

        self.expected_organizations = [
            {
                "category": u"other",
                "dissolution_date": "2011-03-20",
                "founding_date": "2009",
                "contact_details": [],
                "name": u"Test Organisation",
                "classification": u"Example Org Kind",
                "identifiers": [],
                "id": "org.example/core_organisation/{organization_id}",
                "slug": u"test-organisation"
            }
        ]

    def rewrite_field(self, o, key, format_dict):
        o[key] = o[key].format(**format_dict)

    def rewrite_expected_data(self):

        format_dict = {
            'organization_id': self.organisation.id,
            'person_id': self.person.id,
            'position_id': self.position.id,
            'image_name': self.person_image.image.name
        }

        self.rewrite_field(self.expected_persons[0], 'id', format_dict)
        self.rewrite_field(self.expected_persons[0]['images'][0], 'url', format_dict)
        self.rewrite_field(self.expected_organizations[0], 'id', format_dict)
        self.rewrite_field(self.expected_memberships[0], 'id', format_dict)
        self.rewrite_field(self.expected_memberships[0], 'person_id', format_dict)
        self.rewrite_field(self.expected_memberships[0], 'organization_id', format_dict)

    def test_popolo_representation_distinct(self):
        data = get_popolo_data('org.example',
                               'http://pombola.example.org/',
                               inline_memberships=False)

        self.rewrite_expected_data()

        self.assertEqual(data['persons'], self.expected_persons)
        self.assertEqual(data['organizations'], self.expected_organizations)
        self.assertEqual(data['memberships'], self.expected_memberships)

    def test_popolo_representation_inline(self):
        data = get_popolo_data('org.example',
                               'http://pombola.example.org/',
                               inline_memberships=True)

        self.rewrite_expected_data()

        self.assertEqual(1, len(data['persons']))
        self.assertEqual(1, len(data['persons'][0]['memberships']))
        expected_membership = self.expected_memberships[0].copy()
        expected_person = self.expected_persons[0].copy()
        expected_person['memberships'] = [expected_membership]
        self.assertEqual(data['persons'], [expected_person])
        self.assertEqual(data['organizations'], self.expected_organizations)
        self.assertNotIn('memberships', data)

# FIXME: also mock out the PopIt API to test create_organisations and
# create_people.

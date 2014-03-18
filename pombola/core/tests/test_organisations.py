from django.test import TestCase

from pombola.core import models

from django.contrib.contenttypes.models import ContentType

class OrganisationTest(TestCase):
    def setUp(self):
        self.organisation_kind = models.OrganisationKind(
            name = 'Foo',
            slug = 'foo',
        )
        self.organisation_kind.save()

        self.organisation = models.Organisation(
            name = 'Test Org',
            slug = 'test-org',
            kind = self.organisation_kind,
        )
        self.organisation.save()

        self.mysociety_id = models.Identifier.objects.create(
            identifier="/organisations/1",
            scheme="org.mysociety.za",
            object_id=self.organisation.id,
            content_type=ContentType.objects.get_for_model(models.Organisation))

    def testIdentifier(self):
        org_mysociety_id = self.organisation.get_identifier('org.mysociety.za')
        self.assertEqual(org_mysociety_id, '/organisations/1')


    def tearDown(self):
        self.mysociety_id.delete()
        self.organisation.delete()
        self.organisation_kind.delete()

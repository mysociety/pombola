from django.core.urlresolvers import reverse
from django.contrib.contenttypes.models import ContentType
from django.test import TestCase

from pombola.core import models
from pombola.slug_helpers.models import SlugRedirect


class OrganisationKindTest(TestCase):

    def setUp(self):
        # Create some example objects so that the requests don't 404
        # after redirection:
        organisation_kind = models.OrganisationKind.objects.create(
            name='New',
            slug='new',
            )
        models.Organisation.objects.create(
            slug='example-org',
            name='Example Organisation',
            kind=organisation_kind,
            )
        models.PositionTitle.objects.create(
            name='Job Title',
            slug='job-title',
            )

        SlugRedirect.objects.create(
            content_type=ContentType.objects.get_for_model(
                models.OrganisationKind),
            new_object=organisation_kind,
            old_object_slug='old',
            )

    def test_redirect_organisation_kind(self):
        response = self.client.get(
            reverse('organisation_kind', kwargs={'slug': 'old'}),
            )
        self.assertRedirects(
            response,
            reverse('organisation_kind', kwargs={'slug': 'new'}),
            )

    def test_redirect_position_pt_ok(self):
        response = self.client.get(
            reverse('position_pt_ok', kwargs={
                'pt_slug': 'job-title',
                'ok_slug': 'old',
            })
        )
        self.assertRedirects(
            response,
            reverse('position_pt_ok', kwargs={
                'pt_slug': 'job-title',
                'ok_slug': 'new',
            })
        )

    def test_redirect_position_pt_ok_o(self):
        response = self.client.get(
            reverse('position_pt_ok_o', kwargs={
                'pt_slug': 'job-title',
                'ok_slug': 'old',
                'o_slug': 'example-org',
            })
        )
        self.assertRedirects(
            response,
            reverse('position_pt_ok_o', kwargs={
                'pt_slug': 'job-title',
                'ok_slug': 'new',
                'o_slug': 'example-org',
            })
        )

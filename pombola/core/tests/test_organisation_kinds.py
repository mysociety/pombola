from django.core.urlresolvers import reverse
from django.test import TestCase

from pombola.core import models
from pombola.slug_helpers.models import SlugRedirect

from django.contrib.contenttypes.models import ContentType


class OrganisationKindTest(TestCase):
    def test_redirect(self):
        organisation_kind = models.OrganisationKind.objects.create(
            name='New',
            slug='new',
            )

        SlugRedirect.objects.create(
            content_type=ContentType.objects.get_for_model(
                models.OrganisationKind),
            new_object=organisation_kind,
            old_object_slug='old',
            )

        response = self.client.get(
            reverse('organisation_kind', kwargs={'slug': 'old'}),
            )
        self.assertRedirects(
            response,
            reverse('organisation_kind', kwargs={'slug': 'new'}),
            )

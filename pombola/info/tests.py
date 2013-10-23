from django.conf import settings
from django.utils import unittest
from django.test.client import Client
from django.test import TestCase

from .models import InfoPage

class InfoTest(TestCase):

    def setUp(self):
        pass

    def test_get_absolute_url(self):
        page = InfoPage(slug="page", title="Page Title", content="blah", kind=InfoPage.KIND_PAGE)
        post = InfoPage(slug="post", title="Post Title", content="blah", kind=InfoPage.KIND_BLOG)

        self.assertEqual(page.get_absolute_url(), "/info/page")
        self.assertEqual(post.get_absolute_url(), "/blog/post")


    @unittest.skipUnless(settings.COUNTRY_APP == 'south_africa', "Only applies to South Africa")
    def test_info_newsletter_uses_custom_template(self):

        # Create the page entry so that we don't just get a 404
        InfoPage.objects.create(slug="newsletter", title="Newsletter", content="Blah blah")

        # Get the page
        c = Client()
        response = c.get('/info/newsletter')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "south_africa/info_newsletter.html")


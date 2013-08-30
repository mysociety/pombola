from django.conf import settings
# from django.test.client import Client
from django.utils import unittest

from .models import InfoPage

class InfoTest(unittest.TestCase):

    def setUp(self):
        pass

    def test_get_absolute_url(self):
        page = InfoPage(slug="page", title="Page Title", content="blah", kind=InfoPage.KIND_PAGE)
        post = InfoPage(slug="post", title="Post Title", content="blah", kind=InfoPage.KIND_BLOG)

        self.assertEqual(page.get_absolute_url(), "/info/page")
        self.assertEqual(post.get_absolute_url(), "/blog/post")

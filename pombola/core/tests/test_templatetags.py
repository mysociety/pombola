
from django.test import TestCase

from ..templatetags.breadcrumbs import breadcrumbs

class BreadcrumbTest(TestCase):


    def test_breadcrumbs(self):
        """Check that the breadcrumbs are generated as expected"""

        home_li = '<li><a href="/" title="Breadcrumb link to the homepage.">Home</a>  <span class="sep">&raquo;</span>  </li>'

        tests = (
            # input, expected output
            ( '/',        '<li>Home</li>'),
            ( '/foo',     home_li + '<li>Foo</li>'),
            ( '/foo/bar', home_li + '<li><a href="foo/" title="Breadcrumb link to Foo">Foo</a>  <span class="sep">&raquo;</span> </li><li>Bar</li>'),

        )

        for url, expected in tests:
            actual = breadcrumbs(url)
            self.assertEqual(actual, expected)


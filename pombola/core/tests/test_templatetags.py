
from django.test import TestCase

from ..templatetags.breadcrumbs import breadcrumbs, url_name_mappings
from ..templatetags.active_class import active_class


class BreadcrumbTest(TestCase):


    def test_breadcrumbs(self):
        """Check that the breadcrumbs are generated as expected"""

        home_li = '<li><a href="/" title="Breadcrumb link to the homepage.">Home</a>  <span class="sep">&raquo;</span>  </li>'

        tests = (
            # input, expected output
            ( '/',        '<li>Home</li>'),
            ( '/foo',     home_li + '<li>Foo</li>'),
            ( '/foo/bar', home_li + '<li><a href="foo/" title="Breadcrumb link to Foo">Foo</a>  <span class="sep">&raquo;</span> </li><li>Bar</li>'),

            # Test that coordinates are passed through correctly
            # (don't drop '-', put space after ',')
            # See issue #762
            ( '/-1.23,4.56', home_li + '<li>-1.23, 4.56</li>'),
        )

        for url, expected in tests:
            actual = breadcrumbs(url)
            self.assertEqual(actual, expected)

    def test_breadcrumb_url_name_mappings(self):
        for name, title_url in url_name_mappings.iteritems():
            title, url = title_url
            actual = breadcrumbs(name + '/foo')
            self.assertTrue(title in actual, "Expected {0} to be in {1}".format(title, actual))
            self.assertTrue(url in actual, "Expected {0} to be in {1}".format(url, actual))


class ActiveClassTest(TestCase):

    def test_active(self):
        """Check that active is returned when the url matches the input"""

        tests = (
                ('/', 'home', {}),
                ('/place/foo/', 'place', {'slug': 'foo'}),
        )

        for current_url, route_name, kwargs in tests:
            actual = active_class(current_url, route_name, **kwargs)
            self.assertEqual(' active ', actual)

        self.assertEqual(active_class('/foo', 'home'), '')

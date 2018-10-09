# coding=UTF-8

from django.http import QueryDict
from django.template import Context, Template
from django.test import TestCase

from ..templatetags.breadcrumbs import breadcrumbs, path_element_overrides
from ..templatetags.active_class import active_class


class BreadcrumbTest(TestCase):


    def test_breadcrumbs(self):
        """Check that the breadcrumbs are generated as expected"""

        home_li = '<li><a href="/" title="Breadcrumb link to the homepage.">Home</a>  <span class="sep">&raquo;</span> </li>'

        tests = (
            # input, expected output
            ( '/',        '<li>Home</li>'),
            ( '/organisation',     home_li + '<li>Organisations</li>'),
            ( '/organisation/bar', home_li + '<li><a href="/organisation/all/" title="Breadcrumb link to Organisations">Organisations</a>  <span class="sep">&raquo;</span> </li><li>Bar</li>'),

            # existing urls that aren't in the mapping should be linked to.
            ( '/blog/first-post', home_li + '<li><a href="/blog/" title="Breadcrumb link to Blog">Blog</a>  <span class="sep">&raquo;</span> </li><li>First Post</li>'),

            # urls that don't exist shouldn't be linked to.
            ( '/foo/bar', home_li + '<li>Foo  <span class="sep">&raquo;</span> </li><li>Bar</li>'),

            # Test that coordinates are passed through correctly
            # (don't drop '-', put space after ',')
            # See issue #762
            ( '/-1.23,4.56', home_li + '<li>-1.23, 4.56</li>'),

            # Test pombola hansard URLs:
            ( '/hansard/sitting/national_assembly/2013-12-04-09-00-00',
              home_li + '<li><a href="/hansard/" title="Breadcrumb link to Hansard">Hansard</a>  <span class="sep">&raquo;</span> </li><li>Sitting : National Assembly : 2013 12 04 09 00 00</li>'),

            # Test a URL that contains unsafe characters:
            ( '/"foo"<b>bar-baz&others',
              home_li + '<li>&quot;Foo&quot;&lt;B&gt;Bar Baz&amp;Others</li>'),

            # Test a path that includes a unicode character:
            ( u'/person/boss-smiley-☺/',
              home_li + '<li><a href="/person/all/" title="Breadcrumb link to Politicians">Politicians</a>  <span class="sep">&raquo;</span> </li><li>Boss Smiley &#9786;</li>'),
        )

        for url, expected in tests:
            actual = breadcrumbs(url)
            self.assertEqual(actual, expected)

    def test_breadcrumb_path_element_overrides(self):
        for name, title_url in path_element_overrides.iteritems():
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
            self.assertEqual(' ui-tabs-active ui-state-active ', actual)

        self.assertEqual(active_class('/foo', 'home'), '')


class GetFromKeyTest(TestCase):
    def test_gets_existing_key_from_dictionary(self):
        example_dict = {'foo': 'bar'}
        template = Template("{% load get_from_key %}{{ d|get_from_key:'foo' }}")
        self.assertEqual(
            template.render(Context({'d': example_dict})), 'bar')

    def test_fails_if_key_is_not_present(self):
        example_dict = {'foo': 'bar'}
        template = Template("{% load get_from_key %}{{ d|get_from_key:'qux' }}")
        self.assertEqual(
            template.render(Context({'d': example_dict})), '')

    # This is to check that get_from_key works for classes that don't implement
    # get, for example
    def test_gets_dynamically_generated_value_from_key(self):
        example_dict_like = LazyDictLike()
        template = Template("{% load get_from_key %}{{ d|get_from_key:'foo' }}")
        self.assertEqual(
            template.render(Context({'d': example_dict_like})), 'foofoo')


class LazyDictLike(object):
    def __getitem__(self, key):
        return key + key


class AddQueryParameterTest(TestCase):
    def test_adds_query_parameters_when_there_are_none(self):
        request  = RequestFake('')
        template = Template("{% load add_query_parameter %}{% add_query_parameter request 'parameter' 'value' %}")
        self.assertEqual(
            template.render(Context({'request': request})), 'parameter=value')

    def test_adds_query_parameters_to_the_existing_ones(self):
        request  = RequestFake('parameter=value')
        template = Template("{% load add_query_parameter %}{% add_query_parameter request 'foo' 'bar' %}")
        self.assertEqual(
            template.render(Context({'request': request})),
            'foo=bar&parameter=value')

    def test_overwrites_query_parameters_if_they_exist(self):
        request  = RequestFake('parameter=value')
        template = Template("{% load add_query_parameter %}{% add_query_parameter request 'parameter' 'bar' %}")
        self.assertEqual(
            template.render(Context({'request': request})), 'parameter=bar')


class RequestFake:
    def __init__(self, query_parameters):
        self.GET = QueryDict(query_parameters)

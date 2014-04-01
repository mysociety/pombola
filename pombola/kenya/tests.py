from django.core.urlresolvers import reverse

from django_webtest import WebTest

from nose.plugins.attrib import attr

@attr(country='kenya')
class CountyPerformancePageTests(WebTest):

    def test_page_view(self):
        response = self.app.get('/county-performance')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.html.get('a', {'id': 'share-facebook'}))
        self.assertTrue(response.html.get('a', {'id': 'share-twitter'}))

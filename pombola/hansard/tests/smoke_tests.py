from django_webtest import WebTest

from pombola.core import models


class SmokeTests(WebTest):

    def testAllAppearances(self):

        person = models.Person(
            legal_name="Alfred Smith",
            slug='alfred-smith',
        )
        person.save()

        self.app.get('/hansard/person/alfred-smith/appearances/')

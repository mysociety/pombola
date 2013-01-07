import unittest

from components.models import *

from fake_popit import FakePopIt

class PeopleTestsMixin(object):

    def test_get_all_people(self):
        all_people = self.cc.get_all_people()
        self.assertEqual(len(all_people), 3)

    def test_get_person(self):
        some_person = self.cc.get_person("50c60af171ec32dd6e00110f")
        self.assertEqual(unicode(some_person), "<Person: Magerer Kiprono Langat [50c60af171ec32dd6e00110f]>")
        self.assertIsNotNone(some_person)
        same_person_by_name = self.cc.get_person_by_name("Magerer Kiprono Langat")
        self.assertEqual(some_person, same_person_by_name)

    def test_get_positions_for_person(self):
        some_person = self.cc.get_person("50c60af171ec32dd6e00110f")
        positions_for_person = some_person.get_positions()
        self.assertEqual(len(positions_for_person), 1)

    def test_get_position(self):
        some_position = self.cc.get_position("50c60af271ec32dd6e001116")
        self.assertEqual(unicode(some_position), '<Position: Member of Parliament [50c60af271ec32dd6e001116] (2008 to 2013-03-04)>')

    def test_get_organisation(self):
        parliament = self.cc.get_organisation_by_name('Parliament')
        self.assertEqual(unicode(parliament), "<Organisation: Parliament [50c6093771ec32dd6e000453]>")
        self.assertEqual(parliament.popit_id, "50c6093771ec32dd6e000453")

    def test_get_positions_from_organisation(self):
        parliament = self.cc.get_organisation_by_name('Parliament')
        parliament_positions = parliament.get_positions()
        self.assertEqual(len(parliament_positions), 1)

    def test_filter_positions(self):
        all_mps_ever = self.cc.filter_positions_by_title('Member of Parliament')
        self.assertEqual(len(all_mps_ever), 1)

    def test_current_positions_in_parliament(self):
        parliament = self.cc.get_organisation_by_name('Parliament')
        current_parliament_positions = self.cc.filter_current_postitions_in_organisation(parliament)
        self.assertEqual(len(current_parliament_positions), 1)

    def test_mps(self):
        parliament = self.cc.get_organisation_by_name('Parliament')
        self.assertEqual(parliament.popit_id, "50c6093771ec32dd6e000453")

    def test_complete_organisation(self):
        parliament = self.cc.get_organisation_by_name('Parliament')
        if self.cc.api_version == 'v1':
            self.assertIsNone(parliament.category)
            parliament.complete_from_api()
        elif self.cc.api_version == 'v0.1':
            pass
        else:
            raise Exception, "Unknown API version: %s" % (self.cc.api_version,)
        self.assertEqual(parliament.category, 'political')

    def test_complete_person(self):
        some_person = self.cc.get_person("50c60af171ec32dd6e00110f")
        if self.cc.api_version == 'v1':
            self.assertIsNone(some_person.date_of_birth)
        elif self.cc.api_version == 'v0.1':
            pass
        else:
            raise Exception< "Unknown API version: %s" % (self.cc.api_version,)
        some_person.complete_from_api()
        self.assertEqual(str(some_person.date_of_birth), '1973')

    def test_error_missing(self):
        self.assertIsNone(self.cc.get_person('blah'))
        with self.assertRaises(NoSuchPopItObject):
            self.cc.get_organisation_by_name('Society for the Preservation of Django Ponies')

class TestPeopleAPIv1(unittest.TestCase, PeopleTestsMixin):

    def setUp(self):
        fake_popit = FakePopIt(api_version="v1")
        self.cc = ComponentClient(fake_popit)
        self.cc.setup()

class TestPeopleAPIv01(unittest.TestCase, PeopleTestsMixin):

    def setUp(self):
        fake_popit = FakePopIt(api_version="v0.1")
        self.cc = ComponentClient(fake_popit)
        self.cc.setup()

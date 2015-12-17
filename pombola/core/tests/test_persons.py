import datetime

from django_webtest import WebTest
from django.test import TestCase

from django.contrib.contenttypes.models import ContentType

from pombola.core import models
import pombola.scorecards.models


class PersonTest(WebTest):
    def test_naming(self):        
        # create a test person
        person = models.Person(
            legal_name="Alfred Smith"
        )
        person.save()
        self.assertEqual( person.name, "Alfred Smith" )
        self.assertEqual( person.additional_names(), [] )
        self.assertEqual( person.sort_name, "Smith" )

        # Add an alternative name
        person.add_alternative_name("Freddy Smith", name_to_use=True)
        self.assertEqual( person.name, "Freddy Smith" )
        self.assertEqual( person.additional_names(), [] )

        # Add yet another alternative name
        person.add_alternative_name("Fred Smith", name_to_use=True)
        self.assertEqual( person.name, "Fred Smith" )
        self.assertEqual( person.additional_names(), ['Freddy Smith'] )

        # Remove the first of those names:
        person.remove_alternative_name("Fred Smith")
        self.assertEqual( person.name, "Alfred Smith" )
        self.assertEqual( person.additional_names(), ['Freddy Smith'] )

        # Add yet another alternative name
        person.add_alternative_name("\n\nFred Smith\n\n", name_to_use=True)
        self.assertEqual( person.name, "Fred Smith" )
        self.assertEqual( person.additional_names(), ['Freddy Smith'] )

    def test_explicit_sort_name(self):
        person = models.Person(
            legal_name='Ralph Vaughan Williams',
            sort_name='Vaughan Williams')
        person.save()
        self.assertEqual(person.sort_name, 'Vaughan Williams')

    def test_only_query(self):
        at_least_one_person = models.Person.objects.create(
            legal_name='Ralph Vaughan Williams',
            sort_name='Vaughan Williams')
        all_people_id_and_slug = list(models.Person.objects.only('id', 'slug'))
        at_least_one_person.delete()

    def test_urls(self):
        person = models.Person(
            legal_name="Alfred Smith",
            slug='alfred-smith',
        )
        person.save()
        resp = self.app.get('/person/alfred-smith/')
        self.assertContains(resp, person.legal_name)

class PersonScorecardTest(TestCase):
    def setUp(self):    
        # Alf is a person, but with no particular position.
        self.alf = models.Person.objects.create(
            legal_name="Alfred Smith",
            slug='alfred_smith',
            )
        
        self.cat_contactability = pombola.scorecards.models.Category.objects.create(
            name='Contactability',
            slug='contactability',
            synopsis='How easy is it to get in contact with this person',
            description='Contactability description',
            )

        self.cat_ntacdf = pombola.scorecards.models.Category.objects.create(
            name='NTACDF',
            slug='ntacdf',
            synopsis='NTA constituency data',
            description='NTA constituency data description',
            )

        self.alf.scorecard_entries.create(
            category=self.cat_contactability,
            date=datetime.date(2010, 1, 1),
            remark="Very good!",
            score=1,
            )

        # Bob, however, is the MP for Bobsplace.
        self.bob = models.Person.objects.create(
            legal_name="Bob Jones",
            slug='bob_jones',
            )

        self.politician_title = models.PositionTitle.objects.create(
            name='MP',
            slug='mp',
            )

        self.nominated_politician_title = models.PositionTitle.objects.create(
            name='Nominated Member of Parliament',
            slug='nominated-member-parliament',
            )

        self.place_kind_constituency = models.PlaceKind.objects.create(
            name='Constituency',
            )

        self.bobs_place = models.Place.objects.create(
            name="Bob's Place",
            slug='bobs_place',
            kind=self.place_kind_constituency,
            )

        self.bobs_position = models.Position.objects.create(
            person=self.bob,
            place=self.bobs_place,
            category='political',
            title=self.politician_title,
            )
        
        # Bob is average at one thing
        self.bob.scorecard_entries.create(
            category=self.cat_contactability,
            date=datetime.date(2010, 1, 1),
            remark="Vaguely contactable if you know what you're doing.",
            score=0,
            )

        # Bob's constituency data is pretty bad though.
        self.bobs_place.scorecard_entries.create(
            category=self.cat_ntacdf,
            date=datetime.date(2010, 1, 1),
            remark="Nothing much left here, it's all been stolen.",
            score=-1,
            )

        # Charlie is a nominated MP with no constituency
        self.charlie = models.Person.objects.create(
            legal_name='Charlie Brown',
            slug='charlie_brown',
            )

        self.charlies_position = models.Position.objects.create(
            person=self.charlie,
            category='political',
            title=self.nominated_politician_title,
            )

    def testScorecardOverallNonMP(self):
        # import pdb;pdb.set_trace()
        assert self.alf.scorecard_overall() == 1
        assert self.alf.scorecard_overall_as_word() == 'good'

        self.alf.scorecard_entries.create(
            category=self.cat_ntacdf,
            date=datetime.date(2010, 1, 1),
            remark="Awful.",
            score=-1,
            )

        assert self.alf.scorecard_overall() == 0
        assert self.alf.scorecard_overall_as_word() == 'average'

    def testScorecardOverallMP(self):
        assert self.bob.scorecard_overall() == -0.5, "Bob's score: %s" %self.bob.scorecard_overall()
        assert self.bob.scorecard_overall_as_word() == 'bad', "Bob's word: %s" %self.bob.scorecard_overall_as_word()

    def testConstituencies(self):
        assert not self.alf.constituencies()
        assert len(self.bob.constituencies()) == 1, self.bob.constituencies()
        assert self.bob.constituencies()[0].slug == 'bobs_place'

    def testIsMP(self):
        assert self.bob.is_politician()
        assert not self.alf.is_politician()
        assert self.charlie.is_politician()

class PersonIdentifierTest(TestCase):

    def setUp(self):

        self.alf = models.Person.objects.create(
            legal_name="Alfred Smith",
            slug='alfred_smith',
        )

        # Create two identifiers for Alf:
        self.id_a = models.Identifier.objects.create(
            identifier="/alf",
            scheme="org.mysociety.za",
            object_id=self.alf.id,
            content_type=ContentType.objects.get_for_model(models.Person))

        self.id_a = models.Identifier.objects.create(
            identifier="/alf-buggy-duplicate",
            scheme="org.mysociety.za",
            object_id=self.alf.id,
            content_type=ContentType.objects.get_for_model(models.Person))

        self.id_b = models.Identifier.objects.create(
            identifier="/persons/alfred-smith-2983",
            scheme="org.example",
            object_id=self.alf.id,
            content_type=ContentType.objects.get_for_model(models.Person))

        # Create another person with no identifiers:
        self.bob = models.Person.objects.create(
            legal_name="Bob Jones",
            slug='bob_jones',
        )

    def tearDown(self):
        self.id_a.delete()
        self.id_b.delete()
        self.alf.delete()

    def testGetIdentifier(self):
        alf_mysociety_id = self.alf.get_identifier('org.example')
        self.assertEqual(alf_mysociety_id, "/persons/alfred-smith-2983")

    def testGetAmbiguousIdentifier(self):
        with self.assertRaises(models.Identifier.MultipleObjectsReturned):
            self.alf.get_identifier('org.mysociety.za')

    def testGetIdentifiers(self):
        alf_mysociety_ids = self.alf.get_identifiers('org.mysociety.za')
        self.assertEqual(
            sorted(alf_mysociety_ids),
            ['/alf', '/alf-buggy-duplicate'])

    def testGetAllIdentifiers(self):
        d = self.alf.get_all_identifiers()
        self.assertEqual(
            sorted(d.keys()),
            ['org.example', 'org.mysociety.za'])
        self.assertEqual(
            d['org.example'], set(['/persons/alfred-smith-2983']))
        self.assertEqual(
            sorted(d['org.mysociety.za']),
            ['/alf', '/alf-buggy-duplicate'])

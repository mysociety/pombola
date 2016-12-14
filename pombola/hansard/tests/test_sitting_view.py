from django.contrib.auth.models import User
from django_webtest import WebTest

from pombola.core import models
from ..models import Entry, Sitting

class TestSittingView(WebTest):

    fixtures = ['hansard_test_data']

    def setUp(self):
        self.staffuser = User.objects.create(
            username='editor',
            is_staff=True)
        self.person = models.Person.objects.create(
            legal_name="Alfred Smith",
            slug='alfred-smith')
        self.sitting = Sitting.objects.get(
            venue__slug='national_assembly',
            start_date='2010-04-11',
            start_time='09:30:00')
        Entry.objects.create(
            sitting=self.sitting,
            type='speech',
            page_number=1,
            text_counter=1,
            speaker_name='John Smith',
            speaker=self.person,
            content='Good morning, everyone')

    def test_normal_view(self):
        response = self.app.get('/hansard/sitting/national_assembly/2010-04-11-09-30-00')
        self.assertIn('Good morning, everyone', response.content)
        self.assertIn(
            '<strong><a href="/person/alfred-smith/">Alfred Smith</a></strong>',
            response.content)
        self.assertNotIn('John Smith', response.content)

    def test_with_speaker_names_anonymous_user(self):
        response = self.app.get(
            '/hansard/sitting/national_assembly/2010-04-11-09-30-00?show_original_name=1')
        self.assertIn('Good morning, everyone', response.content)
        self.assertIn(
            '<strong><a href="/person/alfred-smith/">Alfred Smith</a></strong>',
            response.content)
        self.assertNotIn('John Smith', response.content)

    def test_with_speaker_names_user_is_staff(self):
        response = self.app.get(
            '/hansard/sitting/national_assembly/2010-04-11-09-30-00?show_original_name=1',
            user=self.staffuser)
        self.assertIn('Good morning, everyone', response.content)
        self.assertIn(
            '<strong><a href="/person/alfred-smith/">Alfred Smith</a></strong>',
            response.content)
        self.assertIn('John Smith', response.content)

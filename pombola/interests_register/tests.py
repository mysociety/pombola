"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""

from django.test import TestCase
from .models import Category, Release

class InterestsRegisterModelTests(TestCase):
    def test_category_creates_own_slug(self):
        cat = Category.objects.create(name="Foo Bar", sort_order=1)
        self.assertEqual(cat.slug, 'foo-bar')

    def test_release_creates_own_slug(self):
        rel = Release.objects.create(name="Foo Bar", date="2013-12-04")
        self.assertEqual(rel.slug, 'foo-bar')

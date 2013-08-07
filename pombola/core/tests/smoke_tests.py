from django_webtest import WebTest
from django.test.client import Client
from django.test import TestCase

from pombola.core import models

class SmokeTests(WebTest):
    def testFront(self):
        self.app.get('/')

    def testRobots(self):
        self.app.get('/robots.txt')

    def testMemcachedStatus(self):
        self.app.get('/status/memcached/')

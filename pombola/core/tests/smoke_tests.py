from django_webtest import WebTest


class SmokeTests(WebTest):
    def testFront(self):
        self.app.get('/')

    def testRobots(self):
        self.app.get('/robots.txt')

    def testMemcachedStatus(self):
        self.app.get('/status/memcached/')

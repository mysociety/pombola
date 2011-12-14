import random

from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import User

from mzalendo.testing.selenium import MzalendoSeleniumTestCase, TwitterSeleniumTestCase
from mzalendo.core.models import Person
from mzalendo.comments2.models import Comment

class CommentTestCase(MzalendoSeleniumTestCase):
    
    fixtures = ['test_data']

    def test_leaving_comment(self):
        driver = self.driver

        random_string = str( random.randint(100000, 999999) )

        # Go to the test person
        self.open_url('/')
        self.open_url('/person/joseph-bloggs#comments')

        # Go to the comments, and then login to add one
        driver.find_element_by_link_text("add your own").click()

        self.login('superuser')

        # fill in the comment and submit
        driver.find_element_by_id("id_title").clear()
        driver.find_element_by_id("id_title").send_keys("This is a test comment " + random_string)
        driver.find_element_by_id("id_comment").clear()
        driver.find_element_by_id("id_comment").send_keys("Test comment content")
        driver.find_element_by_css_selector("input[type=\"submit\"]").click()

        # check that a comment has been created in the database
        bloggs = Person.objects.get(slug="joseph-bloggs")
        comments = bloggs.comments
        self.assertEqual(comments.count(), 1)
        comment = comments.all()[0]

        # Check that we are on the comment page.
        self.assertTrue( comment.get_absolute_url() in driver.current_url )
        self.assertTrue( comment.title in self.page_source )
        
        
class TweetCommentTestCase(TwitterSeleniumTestCase):

    fixtures = ['test_data']

    def test_posting_to_twitter(self):
        driver = self.driver

        # make sure that we are logged in on twitter
        self.twitter_login()
        
        random_string = str( random.randint(100000, 999999) )

        # create the comment
        bloggs = Person.objects.get(slug="joseph-bloggs")
        superuser = User.objects.get(username="superuser")
        comment = Comment(
            content_type = ContentType.objects.get_for_model(bloggs),
            object_id    = bloggs.id,
            title        = 'test title ' + random_string,
            comment      = 'test comment',
            user         = superuser,
            # submit_date  = datetime.datetime.now(),        
        )
        comment.save()        

        # Go to the test person
        self.open_url( comment.get_absolute_url() )
        
        # Tweet the comment - not sure that the selector is specific enough
        driver.switch_to_frame(1)
        driver.find_element_by_css_selector("a.btn").click()
        
        # go through all the windows and stay with the twitter one
        for h in driver.window_handles:
            driver.switch_to_window(h)
            if 'twitter.com/' in driver.current_url: break
    
        # Check that the tweet is ready to send
        self.assertTrue( random_string in driver.find_element_by_id("status").text )

        # use this to submit the tweet
        #driver.find_element_by_css_selector("input.button.submit").click()
        
        driver.close()
        
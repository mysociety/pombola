from datetime import date
import itertools
import mock
from os.path import dirname, join
import re

from django.core.files.storage import FileSystemStorage
from django.core.urlresolvers import reverse
from django.test.utils import override_settings
from django.test import TestCase, Client

from nose.plugins.attrib import attr

from file_archive.models import File
from .migration_helpers import get_first_image_file
from .models import InfoPage, ViewCount


class InfoTest(TestCase):

    def setUp(self):
        pass

    def test_get_absolute_url(self):
        page = InfoPage(slug="page", title="Page Title", markdown_content="blah", kind=InfoPage.KIND_PAGE)
        post = InfoPage(slug="post", title="Post Title", markdown_content="blah", kind=InfoPage.KIND_BLOG)

        self.assertEqual(page.get_absolute_url(), "/info/page")
        self.assertEqual(post.get_absolute_url(), "/blog/post")


    @attr(country='south_africa')
    def test_info_newsletter_uses_custom_template(self):

        # Create the page entry so that we don't just get a 404
        InfoPage.objects.create(slug="newsletter", title="Newsletter", markdown_content="Blah blah")

        # Get the page
        c = Client()
        response = c.get('/info/newsletter')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "south_africa/info_newsletter.html")

    def test_empty_info_page(self):
        empty_post = InfoPage.objects.create(
            slug='empty-of-info',
            title='A page with no content',
            markdown_content='',
            use_raw=False,
            kind=InfoPage.KIND_BLOG
        )
        # At one point with empty markdown_content this would cause an
        # exception, so add this to check for any regression:
        self.assertEqual(empty_post.content_as_html, '')

    @override_settings(INFO_PAGES_ALLOW_RAW_HTML=True)
    def test_blog_raw_html(self):
        danger_post = InfoPage.objects.create(
            slug="danger",
            title="Visualization",
            raw_content='''<h1 class="foo">Hello there</h1>
                <script>alert('hi!');</script>
                <p>blah blah, unclosed paragraph
                <iframe></iframe>
                <div>And then a div...</div>''',
            use_raw=True,
            kind=InfoPage.KIND_BLOG,
        )
        try:
            # For reasons I don't understand, on Travis the result of
            # this has no space between '</script>' and '<p>' but not locally...
            as_html = re.sub(r'(?ms)\s+', ' ', danger_post.content_as_html)
            as_html = re.sub(r'</script><p>', '</script> <p>', as_html)
            self.assertEqual(
                as_html,
                "<div><h1 class=\"foo\">Hello there</h1> <script>alert('hi!');</script> <p>blah blah, unclosed paragraph <iframe></iframe> </p><div>And then a div...</div></div>"
            )
            self.assertEqual(
                re.sub(r'(?ms)\s+', ' ', danger_post.content_as_cleaned_html),
                "<div><h1 class=\"foo\">Hello there</h1> <p>blah blah, unclosed paragraph </p><div>And then a div...</div></div>"
            )
            self.assertEqual(
                re.sub(r'(?ms)\s+', ' ', danger_post.content_as_plain_text),
                "Hello there blah blah, unclosed paragraph And then a div..."
            )
        finally:
            danger_post.delete()

    @override_settings(INFO_PAGES_ALLOW_RAW_HTML=True)
    def test_no_self_closing_tags(self):
        example_post = InfoPage.objects.create(
            slug="post-with-video",
            title="Embedded YouTube Video",
            raw_content='''<h1 class="foo">Hello there</h1>
                <p>An introductory paragraph:
                <iframe></iframe>
                <p>And then a trailing paragraph...</p>''',
            use_raw=True,
            kind=InfoPage.KIND_BLOG,
        )
        self.assertEqual(
            example_post.content_as_html,
            '''<div><h1 class="foo">Hello there</h1>
                <p>An introductory paragraph:
                <iframe></iframe>
                </p><p>And then a trailing paragraph...</p></div>'''
        )


@override_settings(INFO_PAGES_ALLOW_RAW_HTML=True)
class ViewCountsTest(TestCase):

    @mock.patch('pombola.info.views.date')
    def test_blog_post_views_are_counted(self, mockdate=None):
        example_post_1 = InfoPage.objects.create(
            slug="post",
            title="Example title",
            raw_content="Example content",
            use_raw=True,
            kind=InfoPage.KIND_BLOG,
        )

        example_post_2 = InfoPage.objects.create(
            slug="post2",
            title="Example title 2",
            raw_content="Example content 2",
            use_raw=True,
            kind=InfoPage.KIND_BLOG,
        )

        post_1_url = reverse('info_blog', kwargs={'slug': 'post'})
        post_2_url = reverse('info_blog', kwargs={'slug': 'post2'})

        day1 = date(2015, 01, 01)
        day2 = date(2015, 01, 02)

        mockdate.today.return_value = day1

        # The view counts table should be empty.
        self.assertFalse(ViewCount.objects.exists())

        # View the first post once
        self.client.get(post_1_url)

        self.assertEqual(ViewCount.objects.get(page=example_post_1.id, date=day1).count, 1)
        self.assertFalse(ViewCount.objects.filter(page=example_post_2.id).exists())

        # View it a second time, as the logic is different.
        self.client.get(post_1_url)

        self.assertEqual(ViewCount.objects.get(page=example_post_1.id, date=day1).count, 2)
        self.assertFalse(ViewCount.objects.filter(page=example_post_2.id).exists())

        # Now view the other page
        self.client.get(post_2_url)

        self.assertEqual(ViewCount.objects.get(page=example_post_1.id, date=day1).count, 2)
        self.assertEqual(ViewCount.objects.get(page=example_post_2.id, date=day1).count, 1)

        # And view the first page again
        self.client.get(post_1_url)

        self.assertEqual(ViewCount.objects.get(page=example_post_1.id, date=day1).count, 3)
        self.assertEqual(ViewCount.objects.get(page=example_post_2.id, date=day1).count, 1)

        mockdate.today.return_value = day2

        # And view the first page again
        self.client.get(post_1_url)

        self.assertEqual(ViewCount.objects.get(page=example_post_1.id, date=day1).count, 3)
        self.assertEqual(ViewCount.objects.get(page=example_post_2.id, date=day1).count, 1)
        self.assertEqual(ViewCount.objects.get(page=example_post_1.id, date=day2).count, 1)

    @mock.patch('pombola.info.views.date')
    def test_blog_sidebar_popular_posts(self, mockdate=None):
        from .views import BlogMixin

        example_post_1 = InfoPage.objects.create(
            slug="post",
            title="Example title",
            raw_content="Example content",
            use_raw=True,
            kind=InfoPage.KIND_BLOG,
        )

        example_post_2 = InfoPage.objects.create(
            slug="post2",
            title="Example title 2",
            raw_content="Example content 2",
            use_raw=True,
            kind=InfoPage.KIND_BLOG,
        )
        old_post = InfoPage.objects.create(
            slug="oldpost",
            title="Example title 3",
            raw_content="Example content 2",
            use_raw=True,
            kind=InfoPage.KIND_BLOG,
        )

        day1 = date(2015, 01, 01)

        ViewCount.objects.create(
            page=example_post_1,
            count=10,
            date=day1,
            )
        ViewCount.objects.create(
            page=example_post_2,
            count=5,
            date=day1,
            )
        ViewCount.objects.create(
            page=old_post,
            count=100,
            date=date(2000, 1, 1),
            )

        mockdate.today.return_value = day1

        context = BlogMixin().get_context_data()

        self.assertListEqual(
            [x['slug'] for x in context['popular_posts']],
            ['post', 'post2'],
            )


class InfoBlogClientTests(TestCase):
    fixtures = ['sample_blog_posts.json']

    # def test_show_loaded_pages(self):
    #     pages = InfoPage.objects.all()
    #     if len(pages):
    #         for page in pages:
    #             print page
    #     else:
    #         print "no pages found"

    def _test_label(self, tests, url_base):
        c = Client()

        all_contents = list( itertools.chain( *tests.values() ) )
        # print all_contents

        for label, expected_contents in tests.items():
            url = url_base + label
            # print '------------------', url
            response = c.get(url)
            for content in expected_contents:
                # print label, "should contain", content
                self.assertContains(response, content)

            for content in all_contents:
                if content in expected_contents: continue
                # print label, "should not contain", content
                self.assertNotContains(response, content)

    @attr(country='south_africa')
    def test_tags(self):
        self._test_label(
            tests = {
                "birds":   ["Blah Raven blah", "Blah Swan blah"],
                "mammals": ["Blah Black Panther blah", "Blah Polar Bear blah"],
                "birds,mammals": ["Blah Raven blah", "Blah Swan blah", "Blah Black Panther blah", "Blah Polar Bear blah"],
            },
            url_base = '/blog/tag/'
        )

    @attr(country='south_africa')
    def test_categories(self):
        self._test_label(
            tests = {
                "category-1": ["Blah Raven blah", "Blah Polar Bear blah"],
                "category-2": ["Blah Black Panther blah", "Blah Swan blah"],
                "category-1,category-2": ["Blah Raven blah", "Blah Swan blah", "Blah Black Panther blah", "Blah Polar Bear blah"],
            },
            url_base = '/blog/category/'
        )

@override_settings(INFO_PAGES_ALLOW_RAW_HTML=True)
class ExtractFirstImageTests(TestCase):

    def setUp(self):
        storage = FileSystemStorage()
        with open(join(dirname(__file__), 'fixtures', 'bar.png'), 'rb') as f:
            storage_file = storage.save('file_archive/bar.png', f)
        self.uploaded_file = File.objects.create(
            slug='bar2',
            file=storage_file,
        )

    def tearDown(self):
        self.uploaded_file.delete()

    def test_extract_image_should_work(self):
        markdown = "Here's our nice graphic: " \
            "![Graphic](http://www.pa.org.za{0})".format(
                self.uploaded_file.file.url
            )
        example_infographic = InfoPage.objects.create(
            slug="fun-dataviz",
            title="Some fun data visualization",
            markdown_content=markdown,
            use_raw=False,
            kind=InfoPage.KIND_BLOG,
        )
        first_image = get_first_image_file(File, example_infographic)
        self.assertEqual(first_image.id, self.uploaded_file.id)

    def test_image_from_elsewhere(self):
        markdown = "Here's someone else's graphic: " \
            "![Another graphic](http://google.com/blah.png)"
        example_infographic = InfoPage.objects.create(
            slug="a-google-image",
            title="An image from elsewhere",
            markdown_content=markdown,
            use_raw=False,
            kind=InfoPage.KIND_BLOG,
        )
        first_image = get_first_image_file(File, example_infographic)
        self.assertIsNone(first_image)

    def test_extract_no_images(self):
        markdown = "There's no graphic here."
        example_infographic = InfoPage.objects.create(
            slug="boring-text",
            title="*Nothing* of interest here.",
            markdown_content=markdown,
            use_raw=False,
            kind=InfoPage.KIND_BLOG,
        )
        first_image = get_first_image_file(File, example_infographic)
        self.assertIsNone(first_image)

    def test_extract_image_not_found(self):
        markdown = "Here's our nice graphic: " \
            "![Graphic](http://www.pa.org.za/media_root/file_archive/quux.png)"
        example_infographic = InfoPage.objects.create(
            slug="fun-dataviz",
            title="An interesting visualization",
            markdown_content=markdown,
            use_raw=False,
            kind=InfoPage.KIND_BLOG,
        )
        first_image = get_first_image_file(File, example_infographic)
        self.assertIsNone(first_image)

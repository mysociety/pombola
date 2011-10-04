from __future__ import with_statement

import re

from django.core import serializers
from django.db.models.fields import FieldDoesNotExist
from django.forms.models import modelform_factory
from django.template import Template, Context, get_library
from django.test import TestCase, Client
from django.utils.safestring import mark_safe
from django.utils.unittest import skipUnless

from django.contrib import admin

from markitup import settings
from markitup.templatetags.markitup_tags import _get_markitup_context
from markitup.widgets import MarkItUpWidget, MarkupTextarea, AdminMarkItUpWidget

from models import Post, AbstractParent



def test_filter(text, **kwargs):
    return unicode(text) + unicode(kwargs)



class MarkupFieldTests(TestCase):
    def setUp(self):
        self.post = Post.objects.create(title='example post',
                                        body='replace this text')


    def testUnicodeRender(self):
        self.assertEquals(unicode(self.post.body),
                          u'replacement text')


    def testRaw(self):
        self.assertEquals(self.post.body.raw, 'replace this text')


    def testRendered(self):
        self.assertEquals(self.post.body.rendered,
                          u'replacement text')


    def testLoadBack(self):
        post = Post.objects.get(pk=self.post.pk)
        self.assertEquals(post.body.raw, self.post.body.raw)
        self.assertEquals(post.body.rendered, self.post.body.rendered)


    def testAssignToBody(self):
        self.post.body = 'replace this other text'
        self.post.save()
        self.assertEquals(unicode(self.post.body),
                          u'replacement other text')


    def testAssignToRaw(self):
        self.post.body.raw = 'new text, replace this'
        self.post.save()
        self.assertEquals(unicode(self.post.body),
                          u'new text, replacement')


    def testAssignToRendered(self):
        def _invalid_assignment():
            self.post.body.rendered = 'this should fail'
        self.assertRaises(AttributeError, _invalid_assignment)


    def testMarkSafe(self):
        """
        Calling ``mark_safe`` on a ``Markup`` object should have no
        effect, as the ``Markup`` object already handles marking the
        rendered HTML safe on access.

        """
        self.post.body = mark_safe(self.post.body)
        self.assertEquals(self.post.body.raw, 'replace this text')


    def testAbstractInheritance(self):
        """
        Inheriting from an abstract parent class with a MarkupField should not
        cause duplicate _rendered fields to be added.

        """
        class Child(AbstractParent):
            pass

        self.assertEqual(
            [f.name for f in Child._meta.fields],
            ["id", "content", "_content_rendered"])


# TODO
#    def testOverrideFilter(self):
#        self.post.body.save_markup('tests.tests.test_filter',
#                                   some_arg='some_val')
#        self.assertEquals(unicode(self.post.body),
#                          u"**markdown**{'some_arg': 'some_val'}")



class MarkupFieldSerializationTests(TestCase):
    def setUp(self):
        self.post = Post.objects.create(title='example post',
                                        body='replace this thing')
        self.stream = serializers.serialize('json', Post.objects.all())


    def testSerializeJSON(self):
        self.assertEquals(self.stream,
                          '[{"pk": 1, "model": "tests.post", '
                          '"fields": {"body": "replace this thing", '
                          '"_body_rendered": "replacement thing", '
                          '"title": "example post"}}]')


    def testDeserialize(self):
        self.assertEquals(list(serializers.deserialize("json",
                                                       self.stream))[0].object,
                          self.post)



class MarkupFieldFormTests(TestCase):
    def setUp(self):
        self.post = Post(title='example post', body='**markdown**')
        self.form_class = modelform_factory(Post)


    def testWidget(self):
        self.assertEquals(self.form_class().fields['body'].widget.__class__,
                          MarkupTextarea)


    def testFormFieldContents(self):
        form = self.form_class(instance=self.post)
        self.assertEquals(unicode(form['body']),
                          u'<textarea id="id_body" rows="10" cols="40" name="body">**markdown**</textarea>')


    def testAdminFormField(self):
        ma = admin.ModelAdmin(Post, admin.site)
        self.assertEquals(ma.formfield_for_dbfield(
                Post._meta.get_field('body')).widget.__class__,
                          AdminMarkItUpWidget)



class PreviewTests(TestCase):
    def test_preview_filter(self):
        c = Client()
        response = c.post('/markitup/preview/',
                          {'data': 'replace this with something else'})
        self.assertContains(response, 'replacement with something else',
                            status_code=200)


    def test_preview_css(self):
        c = Client()
        response = c.post('/markitup/preview/',
                          {'data': 'replace this with something else'})
        self.assertContains(response, '/static/markitup/preview.css',
                            status_code=200)


    def test_preview_template(self):
        c = Client()
        response = c.post('/markitup/preview/',
                          {'data': 'replace this with something else'})
        self.assertTemplateUsed(response, 'markitup/preview.html')



class MIUTestCase(TestCase):
    def assertIn(self, needle, haystack, reverse=False):
        func = reverse and self.failIf or self.failUnless
        descrip = reverse and 'in' or 'not in'
        func(needle in haystack,
             "'%s' %s '%s'" % (needle, descrip, haystack))


    def render(self, template_string, context_dict=None):
        """A shortcut for testing template output."""
        if context_dict is None:
            context_dict = {}

        c = Context(context_dict)
        t = Template(template_string)
        return t.render(c).strip()



class TemplatefilterTests(MIUTestCase):
    def test_render_markup(self):
        tpl_string = "{% load markitup_tags %}{{ content|render_markup }}"
        self.assertEquals('replacement text', self.render(tpl_string,
                                                          {'content': 'replace this text'}))



class RenderTests(MIUTestCase):
    look_for = '$("#my_id").markItUp(mySettings);'
    auto_preview_override = True


    def test_widget_render(self):
        widget = MarkItUpWidget()
        self.assertIn(self.look_for,
                      widget.render('name', 'value', {'id': 'my_id'}))


    def test_templatetag_render(self):
        template = """{% load markitup_tags %}{% markitup_editor "my_id" %}"""
        self.assertIn(self.look_for,
                      self.render(template))


    def test_per_widget_auto_preview_override(self):
        widget = MarkItUpWidget(auto_preview=self.auto_preview_override)
        self.assertIn(AutoPreviewSettingTests.look_for,
                      widget.render('name', 'value', {'id': 'my_id'}),
                      reverse=not self.auto_preview_override)


    def test_per_ttag_auto_preview_override(self):
        if self.auto_preview_override:
            arg = "auto_preview"
        else:
            arg = "no_auto_preview"
        template = """{%% load markitup_tags %%}{%% markitup_editor "my_id" "%s" %%}""" % (arg,)
        self.assertIn(AutoPreviewSettingTests.look_for,
                      self.render(template),
                      reverse=not self.auto_preview_override)



class AutoPreviewSettingTests(RenderTests):
    look_for = "$('a[title=\"Preview\"]').trigger('mouseup');"
    auto_preview_override = False


    def setUp(self):
        self._old_auto = settings.MARKITUP_AUTO_PREVIEW
        settings.MARKITUP_AUTO_PREVIEW = True


    def tearDown(self):
        settings.MARKITUP_AUTO_PREVIEW = self._old_auto



class TemplatetagMediaUrlTests(MIUTestCase):
    prefix = '/static'


    # helper abstractions so we can reuse same tests for widget and
    # templatetag methods
    def _reset_context(self):
        # monkeypatch a forced recalculation of the template context
        tags = get_library("markitup_tags")
        tags._markitup_context = _get_markitup_context()


    multiple_newlines_re = re.compile('\n+')


    def _compress_newlines(self, s):
        # template includes cause extra newlines in some cases
        # where form.media always outputs only single newlines
        return self.multiple_newlines_re.sub('\n', s)


    def _get_media(self):
        self._reset_context()
        return self._compress_newlines(
            self.render("{% load markitup_tags %}{% markitup_media %}"))


    def _get_css(self):
        self._reset_context()
        return self.render("{% load markitup_tags %}{% markitup_css %}")


    def _get_js(self):
        self._reset_context()
        return self.render("{% load markitup_tags %}{% markitup_js %}")


    # JQUERY_URL settings and resulting link
    jquery_urls = (
        ('jquery.min.js', '/static/jquery.min.js'),
        ('some/path/jquery.min.js', '/static/some/path/jquery.min.js'),
        ('/some/path/jquery.min.js', '/some/path/jquery.min.js'),
        ('http://www.example.com/jquery.min.js', 'http://www.example.com/jquery.min.js'),
        ('https://www.example.com/jquery.min.js', 'https://www.example.com/jquery.min.js'),
        )


    # MARKITUP_SET settings and resulting CSS link
    set_urls = (
        ('some/path', '%(prefix)s/some/path/%(file)s'),
        ('some/path/', '%(prefix)s/some/path/%(file)s'),
        ('/some/path', '/some/path/%(file)s'),
        ('/some/path/', '/some/path/%(file)s'),
        ('http://www.example.com/path', 'http://www.example.com/path/%(file)s'),
        ('http://www.example.com/path/', 'http://www.example.com/path/%(file)s'),
        ('https://www.example.com/path', 'https://www.example.com/path/%(file)s'),
        ('https://www.example.com/path/', 'https://www.example.com/path/%(file)s'),
        )


    skin_urls = set_urls


    def test_all_media(self):
        out = """<link href="%(prefix)s/markitup/skins/simple/style.css" type="text/css" media="screen" rel="stylesheet" />
<link href="%(prefix)s/markitup/sets/default/style.css" type="text/css" media="screen" rel="stylesheet" />
<script type="text/javascript" src="http://ajax.googleapis.com/ajax/libs/jquery/1.6/jquery.min.js"></script>
<script type="text/javascript" src="%(prefix)s/markitup/ajax_csrf.js"></script>
<script type="text/javascript" src="%(prefix)s/markitup/jquery.markitup.js"></script>
<script type="text/javascript" src="%(prefix)s/markitup/sets/default/set.js"></script>""" % {'prefix': self.prefix}
        self.assertEquals(self._get_media(), out)


    def test_jquery_url(self):
        _old_jquery_url = settings.JQUERY_URL
        try:
            for url, link in self.jquery_urls:
                settings.JQUERY_URL = url
                self.assertIn(link, self._get_js())
        finally:
            settings.JQUERY_URL = _old_jquery_url


    def test_set_via_settings(self):
        _old_miu_set = settings.MARKITUP_SET
        try:
            for miu_set, link in self.set_urls:
                css_link = link % {'prefix': self.prefix, 'file': 'style.css'}
                js_link = link % {'prefix': self.prefix, 'file': 'set.js'}
                settings.MARKITUP_SET = miu_set
                self.assertIn(css_link, self._get_css())
                self.assertIn(js_link, self._get_js())
        finally:
            settings.MARKITUP_SET = _old_miu_set


    def test_skin_via_settings(self):
        _old_miu_skin = settings.MARKITUP_SKIN
        try:
            for miu_skin, link in self.skin_urls:
                link = link % {'prefix': self.prefix, 'file': 'style.css'}
                settings.MARKITUP_SKIN = miu_skin
                self.assertIn(link, self._get_css())
        finally:
            settings.MARKITUP_SKIN = _old_miu_skin


class WidgetMediaUrlTests(TemplatetagMediaUrlTests):
    def _get_media_obj(self, *args, **kwargs):
        widget = MarkItUpWidget(*args, **kwargs)
        return widget.media


    def _get_media(self, *args, **kwargs):
        return str(self._get_media_obj(*args, **kwargs))


    def _get_css(self, *args, **kwargs):
        return str(self._get_media_obj(*args, **kwargs)['css'])


    def _get_js(self, *args, **kwargs):
        return str(self._get_media_obj(*args, **kwargs)['js'])


    def test_set_via_argument(self):
        for miu_set, link in self.set_urls:
            css_link = link % {'prefix': self.prefix, 'file': 'style.css'}
            js_link = link % {'prefix': self.prefix, 'file': 'set.js'}
            self.assertIn(css_link, self._get_css(markitup_set=miu_set))
            self.assertIn(js_link, self._get_js(markitup_set=miu_set))


    def test_skin_via_argument(self):
        for miu_skin, link in self.skin_urls:
            link = link % {'prefix': self.prefix, 'file': 'style.css'}
            self.assertIn(link, self._get_css(markitup_skin=miu_skin))



try:
    from south.modelsinspector import introspector
except ImportError:
    introspector = None


class SouthFreezingTests(TestCase):
    @skipUnless(introspector, "South not available")
    def test_introspector_adds_no_rendered_field(self):
        mf = Post._meta.get_field('body')
        args, kwargs = introspector(mf)
        self.assertEquals(kwargs['no_rendered_field'], 'True')

    @skipUnless(introspector, "South not available")
    def test_no_rendered_field_works(self):
        from models import NoRendered
        self.assertRaises(FieldDoesNotExist,
                          NoRendered._meta.get_field,
                          '_body_rendered')

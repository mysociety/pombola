===============
django-markitup
===============

A Django reusable application for end-to-end markup handling. Includes:

* Easy integration of the `MarkItUp!`_ markup editor widget (by Jay
  Salvat) in Django projects, with server-side support for MarkItUp!'s
  AJAX preview. Plug in MarkItUp! via form widget or template tags.

* ``MarkupField``, a ``TextField`` that automatically renders and
  stores both its raw and rendered values in the database, on the
  assumption that disk space is cheaper than CPU cycles in a web
  application.

.. _MarkItUp!: http://markitup.jaysalvat.com/


Installation
============

Install from PyPI with ``easy_install`` or ``pip``::

    pip install django-markitup

or get the `in-development version`_::

    pip install django-markitup==tip

.. _in-development version: http://bitbucket.org/carljm/django-markitup/get/tip.gz#egg=django_markitup-tip

To use ``django-markitup`` in your Django project:

    1. Add ``'markitup'`` to your ``INSTALLED_APPS`` setting.

    2. Make the contents of the ``markitup/static/markitup`` directory
       available at ``STATIC_URL/markitup``; the simplest way is via
       `django.contrib.staticfiles`_.

    3. Set `the MARKITUP_FILTER setting`_.

    4. If you want to use AJAX-based preview, add
          ``url(r'^markitup/', include('markitup.urls'))`` in your root URLconf.

.. _django.contrib.staticfiles: https://docs.djangoproject.com/en/dev/howto/static-files/


Dependencies
------------

``django-markitup`` 1.0 requires `Django`_ 1.3 or later and Python 2.5 or
later. The 0.6.x series supports `Django`_ 1.1 and 1.2; it is missing
1.3-compatibility additions but otherwise has feature-parity with 1.0, so
remains a fine choice for older Django versions.

`MarkItUp!`_ is not an external dependency; it is bundled with
``django-markitup``.

.. _Django: http://www.djangoproject.com/

Using the MarkItUp! widget
==========================

The MarkItUp! widget lives at ``markitup.widgets.MarkItUpWidget``, and
can be used like any other Django custom widget.

To assign it to a form field::

    from markitup.widgets import MarkItUpWidget

    class MyForm(forms.Form):
        content = forms.CharField(widget=MarkItUpWidget())

When this form is displayed on your site, you must include the form
media somewhere on the page using ``{{ form.media }}``, or the
MarkItUpWidget will have no effect.

MarkItUpWidget accepts three optional keyword arguments:
``markitup_set`` and ``markitup_skin`` (see `Choosing a MarkItUp!
button set and skin`_) and ``auto_preview`` (to override the value of
the `MARKITUP_AUTO_PREVIEW`_ setting).

To use the widget in the Django admin::

    from markitup.widgets import AdminMarkItUpWidget

    class MyModelAdmin(admin.ModelAdmin):
    ...
    def formfield_for_dbfield(self, db_field, **kwargs):
        if db_field.name == 'content':
            kwargs['widget'] = AdminMarkItUpWidget()
        return super(MyModelAdmin, self).formfield_for_dbfield(db_field, **kwargs)

You can also use the formfield_overrides attribute of the ModelAdmin, which
is simpler but only allows setting the widget per field type (so it isn't
possible to use the MarkItUpWidget on one TextField in a model and not
another)::

    from markitup.widgets import AdminMarkItUpWidget

    class MyModelAdmin(admin.ModelAdmin):
        formfield_overrides = {models.TextField: {'widget': AdminMarkItUpWidget}}

If you use `MarkupField`_ in your model, it is rendered in the admin
  with an ``AdminMarkItUpWidget`` by default.

Using MarkItUp! via templatetags
================================

In some cases it may be inconvenient to use ``MarkItUpWidget`` (for
instance, if the form in question is defined in third-party code). For
these cases, django-markitup provides template tags to achieve the
same effect purely in templates.

First, load the django-markitup template tag library::

    {% load markitup_tags %}

Then include the MarkItUp! CSS and Javascript in the <head> of your page::

    {% markitup_media %}

By default the ``markitup_media`` tag also includes jQuery, based on
the value of your `JQUERY_URL`_ setting, with a fallback to the
version hosted at Google Ajax APIs. To suppress the inclusion of
jQuery (if you are already including it yourself), pass any non-zero
argument to the tag::

    {% markitup_media "no-jquery" %}

If you prefer to link CSS and Javascript from different locations, the
``markitup_media`` tag can be replaced with two separate tags,
``markitup_css`` and ``markitup_js``. ``markitup_js`` accepts a
parameter to suppress jQuery inclusion, just like
``markitup_media``. (Note that jQuery must be included in your
template before the ``markitup_editor`` tag is used).

Last, use the ``markitup_editor`` template tag to apply the MarkItUp!
editor to a textarea in your page. It accepts one argument, the HTML
id of the textarea. If you are rendering the textarea in the usual way
via a Django form object, that id value is available as
``form.fieldname.auto_id``::

    {{ form.fieldname }}

    {% markitup_editor form.fieldname.auto_id %}

You can use ``markitup_editor`` on as many different textareas as you
like.

``markitup_editor`` accepts an optional second parameter, which can be
either ``"auto_preview"`` or ``"no_auto_preview"`` to override the
value of the `MARKITUP_AUTO_PREVIEW`_ setting.

The actual HTML included by these templatetags is defined by the
contents of the templates ``markitup/include_css.html``,
``markitup/include_js.html``, and ``markitup/editor.html``. You can
override these templates in your project and customize them however
you wish.

MarkupField
===========

You can apply the MarkItUp! editor control to any textarea using the
above techniques, and handle the markup on the server side however you
prefer.

For a seamless markup-handling solution, django-markitup also provides
a ``MarkupField`` model field that automatically renders and stores
both its raw and rendered values in the database, using the value of
`the MARKITUP_FILTER setting`_ to parse the markup into HTML.

A ``MarkupField`` is easy to add to any model definition::

    from django.db import models
    from markitup.fields import MarkupField

    class Article(models.Model):
        title = models.CharField(max_length=100)
        body = MarkupField()

``MarkupField`` automatically creates an extra non-editable field
``_body_rendered`` to store the rendered markup. This field doesn't
need to be accessed directly; see below.

Accessing a MarkupField on a model
----------------------------------

When accessing an attribute of a model that was declared as a
``MarkupField``, a ``Markup`` object is returned.  The ``Markup``
object has two attributes:

``raw``:
    The unrendered markup.
``rendered``:
    The rendered HTML version of ``raw`` (read-only).

This object also has a ``__unicode__`` method that calls
``django.utils.safestring.mark_safe`` on ``rendered``, allowing
``MarkupField`` attributes to appear in templates as rendered HTML
without any special template tag or having to access ``rendered``
directly.

Assuming the ``Article`` model above::

    >>> a = Article.objects.all()[0]
    >>> a.body.raw
    u'*fancy*'
    >>> a.body.rendered
    u'<p><em>fancy</em></p>'
    >>> print unicode(a.body)
    <p><em>fancy</em></p>

Assignment to ``a.body`` is equivalent to assignment to
``a.body.raw``.

.. note::
    a.body.rendered is only updated when a.save() is called

Editing a MarkupField in a form
-------------------------------

When editing a ``MarkupField`` model attribute in a ``ModelForm``
(i.e. in the Django admin), you'll generally want to edit the original
markup and not the rendered HTML.  Because the ``Markup`` object
returns rendered HTML from its __unicode__ method, it's necessary to
use the ``MarkupTextarea`` widget from the ``markupfield.widgets``
module, which knows to return the raw markup instead.

By default, a ``MarkupField`` uses the MarkItUp! editor control in the
admin (via the provided ``AdminMarkItUpWidget``), but a plain
``MarkupTextarea`` in other forms. If you wish to use the MarkItUp!
editor with this ``MarkupField`` in your own form, you'll need to use
the provided ``MarkItUpWidget`` rather than ``MarkupTextarea``.

If you apply your own custom widget to the form field representing a
``MarkupField``, your widget must either inherit from
``MarkupTextarea`` or its ``render`` method must convert its ``value``
argument to ``value.raw``.


Choosing a MarkItUp! button set and skin
========================================

MarkItUp! allows the toolbar button-set to be customized in a
Javascript settings file.  By default, django-markitup uses the
"default" set (meant for HTML editing).  Django-markitup also includes
basic "markdown" and "textile" sets (these are the sets available from
`the MarkItUp site <http://markitup.jaysalvat.com>`_, modified only to
add previewParserPath).

To use an alternate set, assign the ``MARKITUP_SET`` setting a URL path
(absolute or relative to ``STATIC_URL``) to the set directory.  For
instance, to use the "markdown" set included with django-markitup::

    MARKITUP_SET = 'markitup/sets/markdown'

MarkItUp! skins can be specified in a similar manner.  Both "simple"
and "markitup" skins are included, by default "simple" is used.  To
use the "markitup" skin instead::

    MARKITUP_SKIN = 'markitup/skins/markitup'

Neither of these settings has to refer to a location inside
django-markitup's media.  You can define your own sets and skins and
store them anywhere, as long as you set the MARKITUP_SET and
MARKITUP_SKIN settings to the appropriate URLs.

Set and skin may also be chosen on a per-widget basis by passing the
``markitup_set`` and ``markitup_skin`` keyword arguments to
MarkItUpWidget.


Using AJAX preview
==================

If you've included ``markitup.urls`` in your root URLconf (as
demonstrated above under `Installation`_), all you need to enable
server-side AJAX preview is `the MARKITUP_FILTER setting`_.

The rendered HTML content is displayed in the Ajax preview wrapped by
an HTML page generated by the ``markitup/preview.html`` template; you
can override this template in your project and customize the preview
output.

**Note:** If you use your own custom MarkItUp! set, be sure to set the
  ``previewParserPath`` option to ``'/markitup/preview/'``.

The MARKITUP_FILTER setting
===========================

The ``MARKITUP_FILTER`` setting defines how markup is transformed into
HTML on your site. This setting is only required if you are using
``MarkupField`` or MarkItUp! AJAX preview.

``MARKITUP_FILTER`` must be a two-tuple. The first element must be a
string, the Python dotted path to a markup filter function.  This
function should accept markup as its first argument and return HTML.
It may accept other keyword arguments as well.  You may parse your
markup using any method you choose, as long as you can wrap it in a
function that meets these criteria.

The second element must be a dictionary of keyword arguments to pass
to the filter function.  The dictionary may be empty.

For example, if you have python-markdown installed, you could use it
like this::

    MARKITUP_FILTER = ('markdown.markdown', {'safe_mode': True})

Alternatively, you could use the "textile" filter provided by Django
like this::

    MARKITUP_FILTER = ('django.contrib.markup.templatetags.markup.textile', {})

(The textile filter function doesn't accept keyword arguments, so the
kwargs dictionary must be empty in this case.)

``django-markitup`` provides one sample rendering function,
``render_rest`` in the ``markitup.renderers`` module.

render_markup template filter
=============================

If you have set `the MARKITUP_FILTER setting`_ and use the MarkItUp!
AJAX preview, but don't wish to store rendered markup in the database
with `MarkupField`_ (or are using third-party models that don't use
`MarkupField`_), you may want a convenient way to render content in
your templates using your MARKITUP_FILTER function. For this you can
use the ``render_markup`` template filter::

    {% load markitup_tags %}

    {{ post.content|render_markup }}

Other settings
==============

MARKITUP_PREVIEW_FILTER
-----------------------

This optional setting can be used to override the markup filter used
for the Ajax preview view, if for some reason you need it to be
different from the filter used for rendering markup in a
``MarkupField``. It has the same format as ``MARKITUP_FILTER``; by
default it is set equal to ``MARKITUP_FILTER``.

MARKITUP_AUTO_PREVIEW
---------------------

If set to ``True``, the preview window will be activated by
default. Defaults to ``False``.

JQUERY_URL
----------

MarkItUp! requires the jQuery Javascript library.  By default,
django-markitup links to the most recent minor version of jQuery 1.6
available at ajax.googleapis.com (via the URL
``http://ajax.googleapis.com/ajax/libs/jquery/1.6/jquery.min.js``).
If you wish to use a different version of jQuery, or host it yourself,
set the JQUERY_URL setting.  For example::

    JQUERY_URL = 'jquery.min.js'

This will use the jQuery available at STATIC_URL/jquery.min.js. A relative
``JQUERY_URL`` is relative to ``STATIC_URL``.


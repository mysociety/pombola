CHANGES
=======

tip (unreleased)
----------------

1.0.0 (2011.07.11)
------------------

- Removed all compatibility shims for Django versions prior to 1.3, including
  all support for static media at ``MEDIA_URL``, static assets under
  ``media/``, and the ``MARKITUP_MEDIA_URL`` setting.

- Updated to jquery 1.6.

- Added check to avoid double _rendered fields when MarkupField is used on an
  abstract base model class. Fixes #11. Thanks Denis Kolodin for report and
  patch.

- Added compatibility with new AJAX CSRF requirements in Django 1.2.5 and
  1.3. Fixes #7. Thanks zw0rk for the report.

- Added blank=True to MarkupField's auto-added rendered-field to avoid South
  warnings.

- Django 1.3 & staticfiles compatibility: MARKITUP_MEDIA_URL and jQuery URL
  default to STATIC_URL rather than MEDIA_URL, if set.  Static assets now
  available under static/ as well as media/.  Thanks Mikhail Korobov.

- MarkupField.get_db_prep_value updated to take "connection" and "prepared"
  arguments to avoid deprecation warnings under Django 1.3.  Thanks Mikhail
  Korobov.

- enforce minimum length of 3 characters for MarkItUp!-inserted h1 and h2
  underline-style headers (works around bug in python-markdown).  Thanks
  Daemian Mack for the report.

0.6.1 (2010.07.01)
------------------

- Added markitup set for reST. Thanks Jannis Leidel.

- fixed reST renderer to not strip initial headline. Thanks Jannis Leidel.

- prevent mark_safe from mangling Markup objects.

0.6.0 (2010.04.26)
------------------

- remove previously-deprecated markitup_head template tag

- wrap jQuery usage in anonymous function, to be more robust against other
  JS framework code on the page (including other jQuerys).  Thanks Mikhael
  Korneev.

- upgrade to MarkItUp! 1.1.7

- add render_markup template filter

- update to jQuery 1.4 and MarkItUp! 1.1.6

- Add auto_preview option.

- Ajax preview view now uses RequestContext, and additionally passes
  ``MARKITUP_MEDIA_URL`` into the template context. (Previously,
  ``MARKITUP_MEDIA_URL`` was passed as ``MEDIA_URL`` and
  RequestContext was not used). Backwards-incompatible; may require
  change to preview template.

0.5.2 (2009.11.24)
------------------

- Fix setup.py so ``tests`` package is not installed.

0.5.1 (2009.11.18)
------------------

- Added empty ``models.py`` file so ``markitup`` is properly registered in
  ``INSTALLED_APPS``. Fixes issue with ``django-staticfiles`` tip not
  finding media.

0.5 (2009.11.12)
----------------

- Added ``MarkupField`` from http://github.com/carljm/django-markupfield
  (thanks Mike Korobov)

- Deprecated ``markitup_head`` template tag in favor of ``markitup_media``.

- Added ``MARKITUP_MEDIA_URL`` setting to override base of relative media
  URL paths.

0.3 (2009.11.04)
----------------

- added template-tag method for applying MarkItUp! editor (inspired by
  django-wysiwyg)

0.2 (2009.03.18)
----------------

- initial release


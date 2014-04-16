# -*- coding: utf-8 -*-
import os

from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import DataMigration
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils.text import slugify

from pombola.core.models import SlugRedirect

class Migration(DataMigration):

    def forwards(self, orm):
        for f in orm.File.objects.all():
            # The repetition of logic here is as recommended here:
            # https://groups.google.com/d/msg/django-developers/F6cD6a9KX4M/vwAjHzF6DF0J
            ideal_slug = slugify(os.path.basename(
                os.path.splitext(f.file.name)[0]))
            if not ideal_slug:
                raise Exception(
                    u'Creating a slug from {0} failed'.format(f.file.name))
            if f.slug and (ideal_slug != f.slug):
                # Then if there was an old slug, try to create a redirect
                # for it:
                SlugRedirect.objects.create(
                    content_type=ContentType.objects.get_for_model(orm.File),
                    old_object_slug=f.slug,
                    new_object_id=f.id,
                    new_object=f)
            f.slug = ideal_slug
            f.save()

    def backwards(self, orm):
        pass

    models = {
        u'file_archive.file': {
            'Meta': {'object_name': 'File'},
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'auto_now_add': 'True', 'blank': 'True'}),
            'file': ('django.db.models.fields.files.FileField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '50'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'auto_now': 'True', 'blank': 'True'})
        }
    }

    complete_apps = ['file_archive']
    symmetrical = True

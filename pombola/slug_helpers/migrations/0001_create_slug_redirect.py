# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    # The forwards and backwards migrations here are following those
    # suggested in http://stackoverflow.com/a/1770138/223092

    def forwards(self, orm):
        db.rename_table('core_slugredirect', 'slug_helpers_slugredirect')

        if not db.dry_run:
            # For permissions to work properly after migrating
            orm['contenttypes.contenttype'].objects.filter(app_label='core', model='slughelper').update(app_label='slug_helpers')

    def backwards(self, orm):
        db.rename_table('slug_helpers_slugredirect', 'core_slugredirect')

        if not db.dry_run:
            # For permissions to work properly after migrating
            orm['contenttypes.contenttype'].objects.filter(app_label='slug_helpers', model='slughelper').update(app_label='core')

    models = {
        u'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        u'slug_helpers.slugredirect': {
            'Meta': {'unique_together': "(('content_type', 'old_object_slug'),)", 'object_name': 'SlugRedirect'},
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']"}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'new_object_id': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'old_object_slug': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        }
    }

    complete_apps = ['slug_helpers']

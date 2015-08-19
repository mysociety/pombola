# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):

        # Changing field 'Entry.person'
        db.alter_column(u'interests_register_entry', 'person_id', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['core.PopoloPerson']))

    def backwards(self, orm):

        # Changing field 'Entry.person'
        db.alter_column(u'interests_register_entry', 'person_id', self.gf('django.db.models.fields.related.ForeignKey')(null=True, to=orm['core.PopoloPerson']))

    models = {
        u'core.popoloperson': {
            'Meta': {'object_name': 'PopoloPerson', '_ormbases': [u'popolo.Person']},
            'can_be_featured': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'hidden': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            u'person_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['popolo.Person']", 'unique': 'True', 'primary_key': 'True'}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '200'})
        },
        u'interests_register.category': {
            'Meta': {'ordering': "('sort_order', 'name')", 'object_name': 'Category'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '300'}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '50'}),
            'sort_order': ('django.db.models.fields.IntegerField', [], {})
        },
        u'interests_register.entry': {
            'Meta': {'ordering': "('person__legal_name', '-release__date', 'category__sort_order', 'category__name', 'sort_order')", 'object_name': 'Entry'},
            'category': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'entries'", 'to': u"orm['interests_register.Category']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'person': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'interests_register_entries'", 'to': u"orm['core.PopoloPerson']"}),
            'release': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'entries'", 'to': u"orm['interests_register.Release']"}),
            'sort_order': ('django.db.models.fields.IntegerField', [], {})
        },
        u'interests_register.entrylineitem': {
            'Meta': {'object_name': 'EntryLineItem'},
            'entry': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'line_items'", 'to': u"orm['interests_register.Entry']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'key': ('django.db.models.fields.CharField', [], {'max_length': '240'}),
            'value': ('django.db.models.fields.TextField', [], {})
        },
        u'interests_register.release': {
            'Meta': {'ordering': "('date', 'name')", 'object_name': 'Release'},
            'date': ('django.db.models.fields.DateField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '300'}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '50'})
        },
        u'popolo.person': {
            'Meta': {'object_name': 'Person'},
            'additional_name': ('django.db.models.fields.CharField', [], {'max_length': '4000', 'blank': 'True'}),
            'biography': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'birth_date': ('django.db.models.fields.CharField', [], {'max_length': '10', 'blank': 'True'}),
            'created_at': ('model_utils.fields.AutoCreatedField', [], {'default': 'datetime.datetime.now'}),
            'death_date': ('django.db.models.fields.CharField', [], {'max_length': '10', 'blank': 'True'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'null': 'True', 'blank': 'True'}),
            'end_date': ('django.db.models.fields.CharField', [], {'max_length': '10', 'null': 'True', 'blank': 'True'}),
            'family_name': ('django.db.models.fields.CharField', [], {'max_length': '4000', 'blank': 'True'}),
            'gender': ('django.db.models.fields.CharField', [], {'max_length': '128', 'blank': 'True'}),
            'given_name': ('django.db.models.fields.CharField', [], {'max_length': '4000', 'blank': 'True'}),
            'honorific_prefix': ('django.db.models.fields.CharField', [], {'max_length': '128', 'blank': 'True'}),
            'honorific_suffix': ('django.db.models.fields.CharField', [], {'max_length': '128', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'image': ('django.db.models.fields.URLField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '4000'}),
            'patronymic_name': ('django.db.models.fields.CharField', [], {'max_length': '4000', 'blank': 'True'}),
            'sort_name': ('django.db.models.fields.CharField', [], {'max_length': '4000', 'blank': 'True'}),
            'start_date': ('django.db.models.fields.CharField', [], {'max_length': '10', 'null': 'True', 'blank': 'True'}),
            'summary': ('django.db.models.fields.CharField', [], {'max_length': '4000', 'blank': 'True'}),
            'updated_at': ('model_utils.fields.AutoLastModifiedField', [], {'default': 'datetime.datetime.now'})
        }
    }

    complete_apps = ['interests_register']

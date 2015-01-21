# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding field 'Source.list_page'
        db.add_column(u'hansard_source', 'list_page',
                      self.gf('django.db.models.fields.CharField')(max_length=50, null=True, blank=True),
                      keep_default=False)
        # Set the list_page property for those sources where we can
        # make a resonable guess at which list page it came from:
        for source in orm.Source.objects.all():
            if 'plone/national-assembly' in source.url:
                source.list_page = 'national-assembly'
                source.save()
            elif 'plone/senate' in source.url:
                source.list_page = 'senate'
                source.save()
        # For any sources where this didn't help, and there is an
        # associated sitting and venue, use that venue to set
        # list_page:
        venue_slug_to_list_page = {
            'national_assembly': 'national-assembly',
            'senate': 'senate',
        }
        for venue in orm.Venue.objects.all():
            for source in orm.Source.objects.filter(sitting__venue=venue, list_page__isnull=True):
                if venue.slug in venue_slug_to_list_page:
                    source.list_page = venue_slug_to_list_page[venue.slug]
                    source.save()

    def backwards(self, orm):
        # Deleting field 'Source.list_page'
        db.delete_column(u'hansard_source', 'list_page')


    models = {
        u'core.person': {
            'Meta': {'ordering': "['sort_name']", 'object_name': 'Person'},
            '_biography_rendered': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            '_summary_rendered': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'additional_name': ('django.db.models.fields.CharField', [], {'max_length': '300', 'blank': 'True'}),
            'biography': ('markitup.fields.MarkupField', [], {'default': "''", 'no_rendered_field': 'True', 'blank': 'True'}),
            'can_be_featured': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'date_of_birth': ('django_date_extensions.fields.ApproximateDateField', [], {'max_length': '10', 'blank': 'True'}),
            'date_of_death': ('django_date_extensions.fields.ApproximateDateField', [], {'max_length': '10', 'blank': 'True'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'family_name': ('django.db.models.fields.CharField', [], {'max_length': '300', 'blank': 'True'}),
            'gender': ('django.db.models.fields.CharField', [], {'max_length': '20', 'blank': 'True'}),
            'given_name': ('django.db.models.fields.CharField', [], {'max_length': '300', 'blank': 'True'}),
            'hidden': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'honorific_prefix': ('django.db.models.fields.CharField', [], {'max_length': '300', 'blank': 'True'}),
            'honorific_suffix': ('django.db.models.fields.CharField', [], {'max_length': '300', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'legal_name': ('django.db.models.fields.CharField', [], {'max_length': '300'}),
            'national_identity': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '200'}),
            'sort_name': ('django.db.models.fields.CharField', [], {'max_length': '300', 'blank': 'True'}),
            'summary': ('markitup.fields.MarkupField', [], {'default': "''", 'no_rendered_field': 'True', 'blank': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        },
        'hansard.alias': {
            'Meta': {'ordering': "['alias']", 'object_name': 'Alias'},
            'alias': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '200'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'auto_now_add': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'ignored': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'person': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['core.Person']", 'null': 'True', 'blank': 'True'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'auto_now': 'True', 'blank': 'True'})
        },
        'hansard.entry': {
            'Meta': {'ordering': "['sitting', 'text_counter']", 'object_name': 'Entry'},
            'content': ('django.db.models.fields.TextField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'page_number': ('django.db.models.fields.IntegerField', [], {'blank': 'True'}),
            'sitting': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['hansard.Sitting']"}),
            'speaker': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'hansard_entries'", 'null': 'True', 'to': u"orm['core.Person']"}),
            'speaker_name': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'speaker_title': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'text_counter': ('django.db.models.fields.IntegerField', [], {}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '20'})
        },
        'hansard.sitting': {
            'Meta': {'ordering': "['-start_date']", 'object_name': 'Sitting'},
            'end_date': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'end_time': ('django.db.models.fields.TimeField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'source': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['hansard.Source']"}),
            'start_date': ('django.db.models.fields.DateField', [], {}),
            'start_time': ('django.db.models.fields.TimeField', [], {'null': 'True', 'blank': 'True'}),
            'venue': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['hansard.Venue']"})
        },
        'hansard.source': {
            'Meta': {'ordering': "['-date', 'name']", 'object_name': 'Source'},
            'date': ('django.db.models.fields.DateField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_processing_attempt': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'last_processing_success': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'list_page': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '200'}),
            'url': ('django.db.models.fields.URLField', [], {'max_length': '1000'})
        },
        'hansard.venue': {
            'Meta': {'ordering': "['slug']", 'object_name': 'Venue'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '200'}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '50'})
        }
    }

    complete_apps = ['hansard']

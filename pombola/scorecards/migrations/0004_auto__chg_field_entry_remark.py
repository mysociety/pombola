# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Changing field 'Entry.remark'
        db.alter_column('scorecards_entry', 'remark', self.gf('django.db.models.fields.CharField')(max_length=150))


    def backwards(self, orm):
        
        # Changing field 'Entry.remark'
        db.alter_column('scorecards_entry', 'remark', self.gf('django.db.models.fields.CharField')(max_length=50))


    models = {
        'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'scorecards.category': {
            'Meta': {'ordering': "('name',)", 'object_name': 'Category'},
            '_description_rendered': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2012, 1, 24, 20, 55, 17, 811867)', 'auto_now_add': 'True', 'blank': 'True'}),
            'description': ('markitup.fields.MarkupField', [], {'no_rendered_field': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '200'}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '50', 'db_index': 'True'}),
            'synopsis': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2012, 1, 24, 20, 55, 17, 811913)', 'auto_now': 'True', 'blank': 'True'})
        },
        'scorecards.entry': {
            'Meta': {'ordering': "('-date', 'category')", 'unique_together': "(('content_type', 'object_id', 'category', 'date'),)", 'object_name': 'Entry'},
            '_equivalent_remark_rendered': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            '_extended_remark_rendered': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'category': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['scorecards.Category']"}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2012, 1, 24, 20, 55, 17, 812581)', 'auto_now_add': 'True', 'blank': 'True'}),
            'date': ('django.db.models.fields.DateField', [], {}),
            'equivalent_remark': ('markitup.fields.MarkupField', [], {'max_length': '400', 'no_rendered_field': 'True', 'blank': 'True'}),
            'extended_remark': ('markitup.fields.MarkupField', [], {'max_length': '1000', 'no_rendered_field': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'object_id': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'remark': ('django.db.models.fields.CharField', [], {'max_length': '150'}),
            'score': ('django.db.models.fields.IntegerField', [], {}),
            'source_name': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'source_url': ('django.db.models.fields.URLField', [], {'max_length': '200', 'blank': 'True'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2012, 1, 24, 20, 55, 17, 812613)', 'auto_now': 'True', 'blank': 'True'})
        }
    }

    complete_apps = ['scorecards']

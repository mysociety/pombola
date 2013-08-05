# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'Category'
        db.create_table('scorecards_category', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime(2012, 1, 4, 10, 44, 9, 601223), auto_now_add=True, blank=True)),
            ('updated', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime(2012, 1, 4, 10, 44, 9, 601280), auto_now=True, blank=True)),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=200)),
            ('slug', self.gf('django.db.models.fields.SlugField')(unique=True, max_length=50, db_index=True)),
            ('synopsis', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('description', self.gf('markitup.fields.MarkupField')(no_rendered_field=True)),
            ('_description_rendered', self.gf('django.db.models.fields.TextField')(blank=True)),
        ))
        db.send_create_signal('scorecards', ['Category'])

        # Adding model 'Entry'
        db.create_table('scorecards_entry', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime(2012, 1, 4, 10, 44, 9, 602004), auto_now_add=True, blank=True)),
            ('updated', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime(2012, 1, 4, 10, 44, 9, 602032), auto_now=True, blank=True)),
            ('category', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['scorecards.Category'])),
            ('content_type', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['contenttypes.ContentType'])),
            ('object_id', self.gf('django.db.models.fields.PositiveIntegerField')()),
            ('date', self.gf('django.db.models.fields.DateField')()),
            ('remark', self.gf('django.db.models.fields.CharField')(max_length=50)),
            ('score', self.gf('django.db.models.fields.IntegerField')()),
            ('equivalent_remark', self.gf('markitup.fields.MarkupField')(max_length=400, no_rendered_field=True, blank=True)),
            ('source_url', self.gf('django.db.models.fields.URLField')(max_length=200, blank=True)),
            ('source_name', self.gf('django.db.models.fields.CharField')(max_length=200, blank=True)),
            ('_equivalent_remark_rendered', self.gf('django.db.models.fields.TextField')(blank=True)),
        ))
        db.send_create_signal('scorecards', ['Entry'])

        # Adding unique constraint on 'Entry', fields ['content_type', 'object_id', 'category', 'date']
        db.create_unique('scorecards_entry', ['content_type_id', 'object_id', 'category_id', 'date'])


    def backwards(self, orm):
        
        # Removing unique constraint on 'Entry', fields ['content_type', 'object_id', 'category', 'date']
        db.delete_unique('scorecards_entry', ['content_type_id', 'object_id', 'category_id', 'date'])

        # Deleting model 'Category'
        db.delete_table('scorecards_category')

        # Deleting model 'Entry'
        db.delete_table('scorecards_entry')


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
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2012, 1, 4, 10, 44, 9, 601223)', 'auto_now_add': 'True', 'blank': 'True'}),
            'description': ('markitup.fields.MarkupField', [], {'no_rendered_field': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '200'}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '50', 'db_index': 'True'}),
            'synopsis': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2012, 1, 4, 10, 44, 9, 601280)', 'auto_now': 'True', 'blank': 'True'})
        },
        'scorecards.entry': {
            'Meta': {'ordering': "('-date', 'category')", 'unique_together': "(('content_type', 'object_id', 'category', 'date'),)", 'object_name': 'Entry'},
            '_equivalent_remark_rendered': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'category': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['scorecards.Category']"}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2012, 1, 4, 10, 44, 9, 602004)', 'auto_now_add': 'True', 'blank': 'True'}),
            'date': ('django.db.models.fields.DateField', [], {}),
            'equivalent_remark': ('markitup.fields.MarkupField', [], {'max_length': '400', 'no_rendered_field': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'object_id': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'remark': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'score': ('django.db.models.fields.IntegerField', [], {}),
            'source_name': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'source_url': ('django.db.models.fields.URLField', [], {'max_length': '200', 'blank': 'True'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2012, 1, 4, 10, 44, 9, 602032)', 'auto_now': 'True', 'blank': 'True'})
        }
    }

    complete_apps = ['scorecards']

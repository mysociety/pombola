# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):
    
    def forwards(self, orm):
        
        # Adding field 'DataCategory._description_rendered'
        db.add_column('place_data_datacategory', '_description_rendered', self.gf('django.db.models.fields.TextField')(default='', blank=True), keep_default=False)

        # Changing field 'DataCategory.description'
        db.alter_column('place_data_datacategory', 'description', self.gf('markitup.fields.MarkupField')(no_rendered_field=True))

        # Adding field 'Data._equivalent_remark_rendered'
        db.add_column('place_data_data', '_equivalent_remark_rendered', self.gf('django.db.models.fields.TextField')(default='', blank=True), keep_default=False)

        # Adding field 'Data._general_remark_rendered'
        db.add_column('place_data_data', '_general_remark_rendered', self.gf('django.db.models.fields.TextField')(default='', blank=True), keep_default=False)

        # Changing field 'Data.equivalent_remark'
        db.alter_column('place_data_data', 'equivalent_remark', self.gf('markitup.fields.MarkupField')(max_length=400, no_rendered_field=True, blank=True))

        # Changing field 'Data.comparative_remark'
        db.alter_column('place_data_data', 'comparative_remark', self.gf('django.db.models.fields.CharField')(max_length=20, blank=True))

        # Changing field 'Data.general_remark'
        db.alter_column('place_data_data', 'general_remark', self.gf('markitup.fields.MarkupField')(no_rendered_field=True))
    
    
    def backwards(self, orm):
        
        # Deleting field 'DataCategory._description_rendered'
        db.delete_column('place_data_datacategory', '_description_rendered')

        # Changing field 'DataCategory.description'
        db.alter_column('place_data_datacategory', 'description', self.gf('django.db.models.fields.TextField')())

        # Deleting field 'Data._equivalent_remark_rendered'
        db.delete_column('place_data_data', '_equivalent_remark_rendered')

        # Deleting field 'Data._general_remark_rendered'
        db.delete_column('place_data_data', '_general_remark_rendered')

        # Changing field 'Data.equivalent_remark'
        db.alter_column('place_data_data', 'equivalent_remark', self.gf('django.db.models.fields.CharField')(max_length=400, blank=True))

        # Changing field 'Data.comparative_remark'
        db.alter_column('place_data_data', 'comparative_remark', self.gf('django.db.models.fields.CharField')(max_length=400))

        # Changing field 'Data.general_remark'
        db.alter_column('place_data_data', 'general_remark', self.gf('django.db.models.fields.CharField')(max_length=400))
    
    
    models = {
        'contenttypes.contenttype': {
            'Meta': {'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'core.contact': {
            'Meta': {'object_name': 'Contact'},
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2011, 10, 20, 10, 30, 10, 32468)', 'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'kind': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.ContactKind']"}),
            'note': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'object_id': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'source': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '500', 'blank': 'True'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2011, 10, 20, 10, 30, 10, 32734)', 'auto_now': 'True', 'blank': 'True'}),
            'value': ('django.db.models.fields.TextField', [], {})
        },
        'core.contactkind': {
            'Meta': {'object_name': 'ContactKind'},
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2011, 10, 20, 10, 30, 10, 32468)', 'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '200'}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '200', 'db_index': 'True'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2011, 10, 20, 10, 30, 10, 32734)', 'auto_now': 'True', 'blank': 'True'})
        },
        'core.organisation': {
            'Meta': {'object_name': 'Organisation'},
            '_summary_rendered': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2011, 10, 20, 10, 30, 10, 32468)', 'auto_now_add': 'True', 'blank': 'True'}),
            'ended': ('django_date_extensions.fields.ApproximateDateField', [], {'max_length': '10', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'kind': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.OrganisationKind']"}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'original_id': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '200', 'db_index': 'True'}),
            'started': ('django_date_extensions.fields.ApproximateDateField', [], {'max_length': '10', 'blank': 'True'}),
            'summary': ('markitup.fields.MarkupField', [], {'default': "''", 'no_rendered_field': 'True', 'blank': 'True'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2011, 10, 20, 10, 30, 10, 32734)', 'auto_now': 'True', 'blank': 'True'})
        },
        'core.organisationkind': {
            'Meta': {'object_name': 'OrganisationKind'},
            '_summary_rendered': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2011, 10, 20, 10, 30, 10, 32468)', 'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '200'}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '200', 'db_index': 'True'}),
            'summary': ('markitup.fields.MarkupField', [], {'default': "''", 'no_rendered_field': 'True', 'blank': 'True'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2011, 10, 20, 10, 30, 10, 32734)', 'auto_now': 'True', 'blank': 'True'})
        },
        'core.place': {
            'Meta': {'object_name': 'Place'},
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2011, 10, 20, 10, 30, 10, 32468)', 'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'kind': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.PlaceKind']"}),
            'location': ('django.contrib.gis.db.models.fields.PointField', [], {'null': 'True', 'blank': 'True'}),
            'mapit_id': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'organisation': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Organisation']", 'null': 'True', 'blank': 'True'}),
            'original_id': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'parent_place': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'child_places'", 'null': 'True', 'to': "orm['core.Place']"}),
            'shape_url': ('django.db.models.fields.URLField', [], {'max_length': '200', 'blank': 'True'}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '100', 'db_index': 'True'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2011, 10, 20, 10, 30, 10, 32734)', 'auto_now': 'True', 'blank': 'True'})
        },
        'core.placekind': {
            'Meta': {'object_name': 'PlaceKind'},
            '_summary_rendered': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2011, 10, 20, 10, 30, 10, 32468)', 'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '200'}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '200', 'db_index': 'True'}),
            'summary': ('markitup.fields.MarkupField', [], {'default': "''", 'no_rendered_field': 'True', 'blank': 'True'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2011, 10, 20, 10, 30, 10, 32734)', 'auto_now': 'True', 'blank': 'True'})
        },
        'place_data.data': {
            'Meta': {'unique_together': "(('place', 'category', 'date'),)", 'object_name': 'Data'},
            '_equivalent_remark_rendered': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            '_general_remark_rendered': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'category': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['place_data.DataCategory']"}),
            'comparative_remark': ('django.db.models.fields.CharField', [], {'max_length': '20', 'blank': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2011, 10, 20, 10, 30, 10, 60366)', 'auto_now_add': 'True', 'blank': 'True'}),
            'date': ('django.db.models.fields.DateField', [], {}),
            'equivalent_remark': ('markitup.fields.MarkupField', [], {'max_length': '400', 'no_rendered_field': 'True', 'blank': 'True'}),
            'general_remark': ('markitup.fields.MarkupField', [], {'no_rendered_field': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'place': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Place']"}),
            'source_name': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'source_url': ('django.db.models.fields.URLField', [], {'max_length': '200'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2011, 10, 20, 10, 30, 10, 60422)', 'auto_now': 'True', 'blank': 'True'}),
            'value': ('django.db.models.fields.FloatField', [], {})
        },
        'place_data.datacategory': {
            'Meta': {'object_name': 'DataCategory'},
            '_description_rendered': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2011, 10, 20, 10, 30, 10, 59392)', 'auto_now_add': 'True', 'blank': 'True'}),
            'description': ('markitup.fields.MarkupField', [], {'no_rendered_field': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '200'}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '50', 'db_index': 'True'}),
            'synopsis': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2011, 10, 20, 10, 30, 10, 59483)', 'auto_now': 'True', 'blank': 'True'}),
            'value_type': ('django.db.models.fields.CharField', [], {'max_length': '20'})
        }
    }
    
    complete_apps = ['place_data']

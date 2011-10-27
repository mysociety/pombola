# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):
    
    def forwards(self, orm):
        
        # Adding model 'Data'
        db.create_table('place_data_data', (
            ('category', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['place_data.DataCategory'])),
            ('updated', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime(2011, 9, 29, 16, 25, 7, 945724), auto_now=True, blank=True)),
            ('source_name', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime(2011, 9, 29, 16, 25, 7, 945684), auto_now_add=True, blank=True)),
            ('comparative_remark', self.gf('django.db.models.fields.CharField')(max_length=400)),
            ('equivalent_remark', self.gf('django.db.models.fields.CharField')(max_length=400, blank=True)),
            ('value', self.gf('django.db.models.fields.FloatField')()),
            ('source_url', self.gf('django.db.models.fields.URLField')(max_length=200)),
            ('place', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['core.Place'])),
            ('general_remark', self.gf('django.db.models.fields.CharField')(max_length=400)),
            ('date', self.gf('django.db.models.fields.DateField')()),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
        ))
        db.send_create_signal('place_data', ['Data'])

        # Adding model 'DataCategory'
        db.create_table('place_data_datacategory', (
            ('updated', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime(2011, 9, 29, 16, 25, 7, 945216), auto_now=True, blank=True)),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=200)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime(2011, 9, 29, 16, 25, 7, 945178), auto_now_add=True, blank=True)),
            ('slug', self.gf('django.db.models.fields.SlugField')(unique=True, max_length=50, db_index=True)),
            ('synopsis', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('value_type', self.gf('django.db.models.fields.CharField')(max_length=20)),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('description', self.gf('django.db.models.fields.TextField')()),
        ))
        db.send_create_signal('place_data', ['DataCategory'])
    
    
    def backwards(self, orm):
        
        # Deleting model 'Data'
        db.delete_table('place_data_data')

        # Deleting model 'DataCategory'
        db.delete_table('place_data_datacategory')
    
    
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
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2011, 9, 29, 16, 25, 7, 924666)', 'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'kind': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.ContactKind']"}),
            'note': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'object_id': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'source': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '500', 'blank': 'True'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2011, 9, 29, 16, 25, 7, 924710)', 'auto_now': 'True', 'blank': 'True'}),
            'value': ('django.db.models.fields.TextField', [], {})
        },
        'core.contactkind': {
            'Meta': {'object_name': 'ContactKind'},
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2011, 9, 29, 16, 25, 7, 924666)', 'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '200'}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '200', 'db_index': 'True'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2011, 9, 29, 16, 25, 7, 924710)', 'auto_now': 'True', 'blank': 'True'})
        },
        'core.organisation': {
            'Meta': {'object_name': 'Organisation'},
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2011, 9, 29, 16, 25, 7, 924666)', 'auto_now_add': 'True', 'blank': 'True'}),
            'ended': ('django_date_extensions.fields.ApproximateDateField', [], {'max_length': '10', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'kind': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.OrganisationKind']"}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'original_id': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '200', 'db_index': 'True'}),
            'started': ('django_date_extensions.fields.ApproximateDateField', [], {'max_length': '10', 'blank': 'True'}),
            'summary': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2011, 9, 29, 16, 25, 7, 924710)', 'auto_now': 'True', 'blank': 'True'})
        },
        'core.organisationkind': {
            'Meta': {'object_name': 'OrganisationKind'},
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2011, 9, 29, 16, 25, 7, 924666)', 'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '200'}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '200', 'db_index': 'True'}),
            'summary': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2011, 9, 29, 16, 25, 7, 924710)', 'auto_now': 'True', 'blank': 'True'})
        },
        'core.place': {
            'Meta': {'object_name': 'Place'},
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2011, 9, 29, 16, 25, 7, 924666)', 'auto_now_add': 'True', 'blank': 'True'}),
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
            'updated': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2011, 9, 29, 16, 25, 7, 924710)', 'auto_now': 'True', 'blank': 'True'})
        },
        'core.placekind': {
            'Meta': {'object_name': 'PlaceKind'},
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2011, 9, 29, 16, 25, 7, 924666)', 'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '200'}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '200', 'db_index': 'True'}),
            'summary': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2011, 9, 29, 16, 25, 7, 924710)', 'auto_now': 'True', 'blank': 'True'})
        },
        'place_data.data': {
            'Meta': {'unique_together': "(('place', 'category', 'date'),)", 'object_name': 'Data'},
            'category': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['place_data.DataCategory']"}),
            'comparative_remark': ('django.db.models.fields.CharField', [], {'max_length': '400'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2011, 9, 29, 16, 25, 7, 945684)', 'auto_now_add': 'True', 'blank': 'True'}),
            'date': ('django.db.models.fields.DateField', [], {}),
            'equivalent_remark': ('django.db.models.fields.CharField', [], {'max_length': '400', 'blank': 'True'}),
            'general_remark': ('django.db.models.fields.CharField', [], {'max_length': '400'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'place': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Place']"}),
            'source_name': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'source_url': ('django.db.models.fields.URLField', [], {'max_length': '200'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2011, 9, 29, 16, 25, 7, 945724)', 'auto_now': 'True', 'blank': 'True'}),
            'value': ('django.db.models.fields.FloatField', [], {})
        },
        'place_data.datacategory': {
            'Meta': {'object_name': 'DataCategory'},
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2011, 9, 29, 16, 25, 7, 945178)', 'auto_now_add': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '200'}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '50', 'db_index': 'True'}),
            'synopsis': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2011, 9, 29, 16, 25, 7, 945216)', 'auto_now': 'True', 'blank': 'True'}),
            'value_type': ('django.db.models.fields.CharField', [], {'max_length': '20'})
        }
    }
    
    complete_apps = ['place_data']

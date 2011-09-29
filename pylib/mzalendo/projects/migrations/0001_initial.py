# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):
    
    depends_on = (
        ("core", "0024_auto__add_field_positiontitle_requires_place"),
    )

    def forwards(self, orm):
        
        # Adding model 'Project'
        db.create_table('projects_project', (
            ('sector', self.gf('django.db.models.fields.CharField')(max_length=400)),
            ('status', self.gf('django.db.models.fields.CharField')(max_length=400)),
            ('updated', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime(2011, 9, 27, 10, 57, 26, 57463), auto_now=True, blank=True)),
            ('project_name', self.gf('django.db.models.fields.CharField')(max_length=400)),
            ('location_name', self.gf('django.db.models.fields.CharField')(max_length=400)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime(2011, 9, 27, 10, 57, 26, 56035), auto_now_add=True, blank=True)),
            ('estimated_cost', self.gf('django.db.models.fields.FloatField')()),
            ('cdf_index', self.gf('django.db.models.fields.IntegerField')(unique=True)),
            ('expected_output', self.gf('django.db.models.fields.CharField')(max_length=400)),
            ('econ2', self.gf('django.db.models.fields.CharField')(max_length=400)),
            ('total_cost', self.gf('django.db.models.fields.FloatField')()),
            ('location', self.gf('django.contrib.gis.db.models.fields.PointField')()),
            ('activity_to_be_done', self.gf('django.db.models.fields.CharField')(max_length=400)),
            ('remarks', self.gf('django.db.models.fields.CharField')(max_length=400)),
            ('econ1', self.gf('django.db.models.fields.CharField')(max_length=400)),
            ('constituency', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['core.Place'])),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('mtfe_sector', self.gf('django.db.models.fields.CharField')(max_length=400)),
        ))
        db.send_create_signal('projects', ['Project'])
    
    
    def backwards(self, orm):
        
        # Deleting model 'Project'
        db.delete_table('projects_project')
    
    
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
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2011, 9, 27, 10, 57, 26, 37650)', 'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'kind': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.ContactKind']"}),
            'note': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'object_id': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'source': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '500', 'blank': 'True'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2011, 9, 27, 10, 57, 26, 37784)', 'auto_now': 'True', 'blank': 'True'}),
            'value': ('django.db.models.fields.TextField', [], {})
        },
        'core.contactkind': {
            'Meta': {'object_name': 'ContactKind'},
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2011, 9, 27, 10, 57, 26, 37650)', 'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '200'}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '200', 'db_index': 'True'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2011, 9, 27, 10, 57, 26, 37784)', 'auto_now': 'True', 'blank': 'True'})
        },
        'core.organisation': {
            'Meta': {'object_name': 'Organisation'},
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2011, 9, 27, 10, 57, 26, 37650)', 'auto_now_add': 'True', 'blank': 'True'}),
            'ended': ('django_date_extensions.fields.ApproximateDateField', [], {'max_length': '10', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'kind': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.OrganisationKind']"}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'original_id': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '200', 'db_index': 'True'}),
            'started': ('django_date_extensions.fields.ApproximateDateField', [], {'max_length': '10', 'blank': 'True'}),
            'summary': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2011, 9, 27, 10, 57, 26, 37784)', 'auto_now': 'True', 'blank': 'True'})
        },
        'core.organisationkind': {
            'Meta': {'object_name': 'OrganisationKind'},
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2011, 9, 27, 10, 57, 26, 37650)', 'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '200'}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '200', 'db_index': 'True'}),
            'summary': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2011, 9, 27, 10, 57, 26, 37784)', 'auto_now': 'True', 'blank': 'True'})
        },
        'core.place': {
            'Meta': {'object_name': 'Place'},
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2011, 9, 27, 10, 57, 26, 37650)', 'auto_now_add': 'True', 'blank': 'True'}),
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
            'updated': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2011, 9, 27, 10, 57, 26, 37784)', 'auto_now': 'True', 'blank': 'True'})
        },
        'core.placekind': {
            'Meta': {'object_name': 'PlaceKind'},
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2011, 9, 27, 10, 57, 26, 37650)', 'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '200'}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '200', 'db_index': 'True'}),
            'summary': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2011, 9, 27, 10, 57, 26, 37784)', 'auto_now': 'True', 'blank': 'True'})
        },
        'projects.project': {
            'Meta': {'object_name': 'Project'},
            'activity_to_be_done': ('django.db.models.fields.CharField', [], {'max_length': '400'}),
            'cdf_index': ('django.db.models.fields.IntegerField', [], {'unique': 'True'}),
            'constituency': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Place']"}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2011, 9, 27, 10, 57, 26, 56035)', 'auto_now_add': 'True', 'blank': 'True'}),
            'econ1': ('django.db.models.fields.CharField', [], {'max_length': '400'}),
            'econ2': ('django.db.models.fields.CharField', [], {'max_length': '400'}),
            'estimated_cost': ('django.db.models.fields.FloatField', [], {}),
            'expected_output': ('django.db.models.fields.CharField', [], {'max_length': '400'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'location': ('django.contrib.gis.db.models.fields.PointField', [], {}),
            'location_name': ('django.db.models.fields.CharField', [], {'max_length': '400'}),
            'mtfe_sector': ('django.db.models.fields.CharField', [], {'max_length': '400'}),
            'project_name': ('django.db.models.fields.CharField', [], {'max_length': '400'}),
            'remarks': ('django.db.models.fields.CharField', [], {'max_length': '400'}),
            'sector': ('django.db.models.fields.CharField', [], {'max_length': '400'}),
            'status': ('django.db.models.fields.CharField', [], {'max_length': '400'}),
            'total_cost': ('django.db.models.fields.FloatField', [], {}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2011, 9, 27, 10, 57, 26, 57463)', 'auto_now': 'True', 'blank': 'True'})
        }
    }
    
    complete_apps = ['projects']

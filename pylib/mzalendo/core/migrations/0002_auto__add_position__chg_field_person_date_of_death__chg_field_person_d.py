# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):
    
    def forwards(self, orm):
        
        # Adding model 'Position'
        db.create_table('core_position', (
            ('end_date', self.gf('django_date_extensions.fields.ApproximateDateField')(max_length=10, blank=True)),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('organisation', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['core.Organisation'])),
            ('start_date', self.gf('django_date_extensions.fields.ApproximateDateField')(max_length=10, blank=True)),
            ('person', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['core.Person'])),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
        ))
        db.send_create_signal('core', ['Position'])

        # Changing field 'Person.date_of_death'
        db.alter_column('core_person', 'date_of_death', self.gf('django_date_extensions.fields.ApproximateDateField')(max_length=10, blank=True))

        # Changing field 'Person.date_of_birth'
        db.alter_column('core_person', 'date_of_birth', self.gf('django_date_extensions.fields.ApproximateDateField')(max_length=10, blank=True))

        # Changing field 'Organisation.started'
        db.alter_column('core_organisation', 'started', self.gf('django_date_extensions.fields.ApproximateDateField')(max_length=10, blank=True))

        # Changing field 'Organisation.ended'
        db.alter_column('core_organisation', 'ended', self.gf('django_date_extensions.fields.ApproximateDateField')(max_length=10, blank=True))
    
    
    def backwards(self, orm):
        
        # Deleting model 'Position'
        db.delete_table('core_position')

        # Changing field 'Person.date_of_death'
        db.alter_column('core_person', 'date_of_death', self.gf('django_date_extensions.fields.ApproximateDateField')(max_length=10))

        # Changing field 'Person.date_of_birth'
        db.alter_column('core_person', 'date_of_birth', self.gf('django_date_extensions.fields.ApproximateDateField')(max_length=10))

        # Changing field 'Organisation.started'
        db.alter_column('core_organisation', 'started', self.gf('django_date_extensions.fields.ApproximateDateField')(max_length=10))

        # Changing field 'Organisation.ended'
        db.alter_column('core_organisation', 'ended', self.gf('django_date_extensions.fields.ApproximateDateField')(max_length=10))
    
    
    models = {
        'core.organisation': {
            'Meta': {'object_name': 'Organisation'},
            'ended': ('django_date_extensions.fields.ApproximateDateField', [], {'max_length': '10', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'organisation_type': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '200', 'db_index': 'True'}),
            'started': ('django_date_extensions.fields.ApproximateDateField', [], {'max_length': '10', 'blank': 'True'})
        },
        'core.person': {
            'Meta': {'object_name': 'Person'},
            'date_of_birth': ('django_date_extensions.fields.ApproximateDateField', [], {'max_length': '10', 'blank': 'True'}),
            'date_of_death': ('django_date_extensions.fields.ApproximateDateField', [], {'max_length': '10', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'gender': ('django.db.models.fields.CharField', [], {'max_length': '1'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'middle_names': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '200', 'db_index': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '20'})
        },
        'core.place': {
            'Meta': {'object_name': 'Place'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'location': ('django.contrib.gis.db.models.fields.PointField', [], {'null': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'organisation': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Organisation']", 'null': 'True'}),
            'place_type': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'shape_url': ('django.db.models.fields.URLField', [], {'max_length': '200', 'blank': 'True'}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '100', 'db_index': 'True'})
        },
        'core.position': {
            'Meta': {'object_name': 'Position'},
            'end_date': ('django_date_extensions.fields.ApproximateDateField', [], {'max_length': '10', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'organisation': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Organisation']"}),
            'person': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Person']"}),
            'start_date': ('django_date_extensions.fields.ApproximateDateField', [], {'max_length': '10', 'blank': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '200'})
        }
    }
    
    complete_apps = ['core']

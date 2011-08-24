# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):
    
    def forwards(self, orm):
        
        # Adding field 'InformationSource.updated'
        db.add_column('core_informationsource', 'updated', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime(2011, 8, 24, 9, 32, 21, 421463), auto_now=True, blank=True), keep_default=False)

        # Adding field 'InformationSource.created'
        db.add_column('core_informationsource', 'created', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime(2011, 8, 24, 9, 32, 21, 421369), auto_now_add=True, blank=True), keep_default=False)

        # Adding field 'ContactKind.updated'
        db.add_column('core_contactkind', 'updated', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime(2011, 8, 24, 9, 32, 21, 421463), auto_now=True, blank=True), keep_default=False)

        # Adding field 'ContactKind.created'
        db.add_column('core_contactkind', 'created', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime(2011, 8, 24, 9, 32, 21, 421369), auto_now_add=True, blank=True), keep_default=False)

        # Adding field 'Place.created'
        db.add_column('core_place', 'created', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime(2011, 8, 24, 9, 32, 21, 421369), auto_now_add=True, blank=True), keep_default=False)

        # Adding field 'Place.updated'
        db.add_column('core_place', 'updated', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime(2011, 8, 24, 9, 32, 21, 421463), auto_now=True, blank=True), keep_default=False)

        # Adding field 'Person.updated'
        db.add_column('core_person', 'updated', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime(2011, 8, 24, 9, 32, 21, 421463), auto_now=True, blank=True), keep_default=False)

        # Adding field 'Person.created'
        db.add_column('core_person', 'created', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime(2011, 8, 24, 9, 32, 21, 421369), auto_now_add=True, blank=True), keep_default=False)

        # Adding field 'Position.updated'
        db.add_column('core_position', 'updated', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime(2011, 8, 24, 9, 32, 21, 421463), auto_now=True, blank=True), keep_default=False)

        # Adding field 'Position.created'
        db.add_column('core_position', 'created', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime(2011, 8, 24, 9, 32, 21, 421369), auto_now_add=True, blank=True), keep_default=False)

        # Adding field 'PositionTitle.updated'
        db.add_column('core_positiontitle', 'updated', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime(2011, 8, 24, 9, 32, 21, 421463), auto_now=True, blank=True), keep_default=False)

        # Adding field 'PositionTitle.created'
        db.add_column('core_positiontitle', 'created', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime(2011, 8, 24, 9, 32, 21, 421369), auto_now_add=True, blank=True), keep_default=False)

        # Adding field 'OrganisationKind.updated'
        db.add_column('core_organisationkind', 'updated', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime(2011, 8, 24, 9, 32, 21, 421463), auto_now=True, blank=True), keep_default=False)

        # Adding field 'OrganisationKind.created'
        db.add_column('core_organisationkind', 'created', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime(2011, 8, 24, 9, 32, 21, 421369), auto_now_add=True, blank=True), keep_default=False)

        # Adding field 'PlaceKind.updated'
        db.add_column('core_placekind', 'updated', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime(2011, 8, 24, 9, 32, 21, 421463), auto_now=True, blank=True), keep_default=False)

        # Adding field 'PlaceKind.created'
        db.add_column('core_placekind', 'created', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime(2011, 8, 24, 9, 32, 21, 421369), auto_now_add=True, blank=True), keep_default=False)

        # Adding field 'Contact.updated'
        db.add_column('core_contact', 'updated', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime(2011, 8, 24, 9, 32, 21, 421463), auto_now=True, blank=True), keep_default=False)

        # Adding field 'Contact.created'
        db.add_column('core_contact', 'created', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime(2011, 8, 24, 9, 32, 21, 421369), auto_now_add=True, blank=True), keep_default=False)

        # Adding field 'Organisation.created'
        db.add_column('core_organisation', 'created', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime(2011, 8, 24, 9, 32, 21, 421369), auto_now_add=True, blank=True), keep_default=False)

        # Adding field 'Organisation.updated'
        db.add_column('core_organisation', 'updated', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime(2011, 8, 24, 9, 32, 21, 421463), auto_now=True, blank=True), keep_default=False)
    
    
    def backwards(self, orm):
        
        # Deleting field 'InformationSource.updated'
        db.delete_column('core_informationsource', 'updated')

        # Deleting field 'InformationSource.created'
        db.delete_column('core_informationsource', 'created')

        # Deleting field 'ContactKind.updated'
        db.delete_column('core_contactkind', 'updated')

        # Deleting field 'ContactKind.created'
        db.delete_column('core_contactkind', 'created')

        # Deleting field 'Place.created'
        db.delete_column('core_place', 'created')

        # Deleting field 'Place.updated'
        db.delete_column('core_place', 'updated')

        # Deleting field 'Person.updated'
        db.delete_column('core_person', 'updated')

        # Deleting field 'Person.created'
        db.delete_column('core_person', 'created')

        # Deleting field 'Position.updated'
        db.delete_column('core_position', 'updated')

        # Deleting field 'Position.created'
        db.delete_column('core_position', 'created')

        # Deleting field 'PositionTitle.updated'
        db.delete_column('core_positiontitle', 'updated')

        # Deleting field 'PositionTitle.created'
        db.delete_column('core_positiontitle', 'created')

        # Deleting field 'OrganisationKind.updated'
        db.delete_column('core_organisationkind', 'updated')

        # Deleting field 'OrganisationKind.created'
        db.delete_column('core_organisationkind', 'created')

        # Deleting field 'PlaceKind.updated'
        db.delete_column('core_placekind', 'updated')

        # Deleting field 'PlaceKind.created'
        db.delete_column('core_placekind', 'created')

        # Deleting field 'Contact.updated'
        db.delete_column('core_contact', 'updated')

        # Deleting field 'Contact.created'
        db.delete_column('core_contact', 'created')

        # Deleting field 'Organisation.created'
        db.delete_column('core_organisation', 'created')

        # Deleting field 'Organisation.updated'
        db.delete_column('core_organisation', 'updated')
    
    
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
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2011, 8, 24, 9, 32, 21, 421369)', 'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'kind': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.ContactKind']"}),
            'note': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'object_id': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'source': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '500', 'blank': 'True'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2011, 8, 24, 9, 32, 21, 421463)', 'auto_now': 'True', 'blank': 'True'}),
            'value': ('django.db.models.fields.TextField', [], {})
        },
        'core.contactkind': {
            'Meta': {'object_name': 'ContactKind'},
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2011, 8, 24, 9, 32, 21, 421369)', 'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '200'}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '200', 'db_index': 'True'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2011, 8, 24, 9, 32, 21, 421463)', 'auto_now': 'True', 'blank': 'True'})
        },
        'core.informationsource': {
            'Meta': {'object_name': 'InformationSource'},
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2011, 8, 24, 9, 32, 21, 421369)', 'auto_now_add': 'True', 'blank': 'True'}),
            'entered': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'note': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'object_id': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'source': ('django.db.models.fields.CharField', [], {'max_length': '500'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2011, 8, 24, 9, 32, 21, 421463)', 'auto_now': 'True', 'blank': 'True'})
        },
        'core.organisation': {
            'Meta': {'object_name': 'Organisation'},
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2011, 8, 24, 9, 32, 21, 421369)', 'auto_now_add': 'True', 'blank': 'True'}),
            'ended': ('django_date_extensions.fields.ApproximateDateField', [], {'max_length': '10', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'kind': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.OrganisationKind']"}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'original_id': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '200', 'db_index': 'True'}),
            'started': ('django_date_extensions.fields.ApproximateDateField', [], {'max_length': '10', 'blank': 'True'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2011, 8, 24, 9, 32, 21, 421463)', 'auto_now': 'True', 'blank': 'True'})
        },
        'core.organisationkind': {
            'Meta': {'object_name': 'OrganisationKind'},
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2011, 8, 24, 9, 32, 21, 421369)', 'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '200'}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '200', 'db_index': 'True'}),
            'summary': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2011, 8, 24, 9, 32, 21, 421463)', 'auto_now': 'True', 'blank': 'True'})
        },
        'core.person': {
            'Meta': {'object_name': 'Person'},
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2011, 8, 24, 9, 32, 21, 421369)', 'auto_now_add': 'True', 'blank': 'True'}),
            'date_of_birth': ('django_date_extensions.fields.ApproximateDateField', [], {'max_length': '10', 'blank': 'True'}),
            'date_of_death': ('django_date_extensions.fields.ApproximateDateField', [], {'max_length': '10', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'gender': ('django.db.models.fields.CharField', [], {'max_length': '1'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'middle_names': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'original_id': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '200', 'db_index': 'True'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2011, 8, 24, 9, 32, 21, 421463)', 'auto_now': 'True', 'blank': 'True'})
        },
        'core.place': {
            'Meta': {'object_name': 'Place'},
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2011, 8, 24, 9, 32, 21, 421369)', 'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'kind': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.PlaceKind']"}),
            'location': ('django.contrib.gis.db.models.fields.PointField', [], {'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'organisation': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Organisation']", 'null': 'True', 'blank': 'True'}),
            'original_id': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'shape_url': ('django.db.models.fields.URLField', [], {'max_length': '200', 'blank': 'True'}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '100', 'db_index': 'True'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2011, 8, 24, 9, 32, 21, 421463)', 'auto_now': 'True', 'blank': 'True'})
        },
        'core.placekind': {
            'Meta': {'object_name': 'PlaceKind'},
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2011, 8, 24, 9, 32, 21, 421369)', 'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '200'}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '200', 'db_index': 'True'}),
            'summary': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2011, 8, 24, 9, 32, 21, 421463)', 'auto_now': 'True', 'blank': 'True'})
        },
        'core.position': {
            'Meta': {'object_name': 'Position'},
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2011, 8, 24, 9, 32, 21, 421369)', 'auto_now_add': 'True', 'blank': 'True'}),
            'end_date': ('django_date_extensions.fields.ApproximateDateField', [], {'max_length': '10', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'note': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '300', 'blank': 'True'}),
            'organisation': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Organisation']", 'null': 'True', 'blank': 'True'}),
            'person': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Person']"}),
            'place': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Place']", 'null': 'True', 'blank': 'True'}),
            'start_date': ('django_date_extensions.fields.ApproximateDateField', [], {'max_length': '10', 'blank': 'True'}),
            'title': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.PositionTitle']", 'null': 'True', 'blank': 'True'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2011, 8, 24, 9, 32, 21, 421463)', 'auto_now': 'True', 'blank': 'True'})
        },
        'core.positiontitle': {
            'Meta': {'object_name': 'PositionTitle'},
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2011, 8, 24, 9, 32, 21, 421369)', 'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '200'}),
            'original_id': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '200', 'db_index': 'True'}),
            'summary': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2011, 8, 24, 9, 32, 21, 421463)', 'auto_now': 'True', 'blank': 'True'})
        },
        'images.image': {
            'Meta': {'object_name': 'Image'},
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'image': ('sorl.thumbnail.fields.ImageField', [], {'max_length': '100'}),
            'is_primary': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'object_id': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'source': ('django.db.models.fields.CharField', [], {'max_length': '400'})
        }
    }
    
    complete_apps = ['core']

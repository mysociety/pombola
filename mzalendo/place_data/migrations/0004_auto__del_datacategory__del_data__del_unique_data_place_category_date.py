# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Removing unique constraint on 'Data', fields ['place', 'category', 'date']
        # db.delete_unique('place_data_data', ['place_id', 'category_id', 'date'])

        # Deleting model 'DataCategory'
        db.delete_table('place_data_datacategory')

        # Deleting model 'Data'
        db.delete_table('place_data_data')


    def backwards(self, orm):
        
        # Adding model 'DataCategory'
        db.create_table('place_data_datacategory', (
            ('_description_rendered', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('synopsis', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('slug', self.gf('django.db.models.fields.SlugField')(max_length=50, unique=True, db_index=True)),
            ('updated', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime(2011, 10, 20, 10, 30, 10, 59483), auto_now=True, blank=True)),
            ('description', self.gf('markitup.fields.MarkupField')(no_rendered_field=True)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime(2011, 10, 20, 10, 30, 10, 59392), auto_now_add=True, blank=True)),
            ('value_type', self.gf('django.db.models.fields.CharField')(max_length=20)),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=200, unique=True)),
        ))
        db.send_create_signal('place_data', ['DataCategory'])

        # Adding model 'Data'
        db.create_table('place_data_data', (
            ('equivalent_remark', self.gf('markitup.fields.MarkupField')(blank=True, max_length=400, no_rendered_field=True)),
            ('source_name', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('_general_remark_rendered', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('updated', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime(2011, 10, 20, 10, 30, 10, 60422), auto_now=True, blank=True)),
            ('source_url', self.gf('django.db.models.fields.URLField')(max_length=200)),
            ('general_remark', self.gf('markitup.fields.MarkupField')(no_rendered_field=True)),
            ('date', self.gf('django.db.models.fields.DateField')()),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('category', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['place_data.DataCategory'])),
            ('created', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime(2011, 10, 20, 10, 30, 10, 60366), auto_now_add=True, blank=True)),
            ('_equivalent_remark_rendered', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('comparative_remark', self.gf('django.db.models.fields.CharField')(max_length=20, blank=True)),
            ('value', self.gf('django.db.models.fields.FloatField')()),
            ('place', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['core.Place'])),
        ))
        db.send_create_signal('place_data', ['Data'])

        # Adding unique constraint on 'Data', fields ['place', 'category', 'date']
        db.create_unique('place_data_data', ['place_id', 'category_id', 'date'])


    models = {
        
    }

    complete_apps = ['place_data']

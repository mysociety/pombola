# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Deleting model 'Chunk'
        db.delete_table('hansard_chunk')


    def backwards(self, orm):
        
        # Adding model 'Chunk'
        db.create_table('hansard_chunk', (
            ('content', self.gf('django.db.models.fields.TextField')()),
            ('source', self.gf('django.db.models.fields.CharField')(max_length=500)),
            ('speaker', self.gf('django.db.models.fields.CharField')(max_length=200, blank=True)),
            ('session', self.gf('django.db.models.fields.CharField')(max_length=2)),
            ('text_counter', self.gf('django.db.models.fields.IntegerField')()),
            ('date', self.gf('django.db.models.fields.DateField')()),
            ('type', self.gf('django.db.models.fields.CharField')(max_length=20)),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('page', self.gf('django.db.models.fields.IntegerField')()),
        ))
        db.send_create_signal('hansard', ['Chunk'])


    models = {
        
    }

    complete_apps = ['hansard']

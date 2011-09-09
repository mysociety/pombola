# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):
    
    def forwards(self, orm):
        
        # Adding model 'Chunk'
        db.create_table('hansard_chunk', (
            ('source', self.gf('django.db.models.fields.CharField')(max_length=500)),
            ('page', self.gf('django.db.models.fields.IntegerField')()),
            ('content', self.gf('django.db.models.fields.TextField')()),
            ('text_counter', self.gf('django.db.models.fields.IntegerField')()),
            ('session', self.gf('django.db.models.fields.CharField')(max_length=2)),
            ('speaker', self.gf('django.db.models.fields.CharField')(max_length=200, blank=True)),
            ('date', self.gf('django.db.models.fields.DateField')()),
            ('type', self.gf('django.db.models.fields.CharField')(max_length=20)),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
        ))
        db.send_create_signal('hansard', ['Chunk'])
    
    
    def backwards(self, orm):
        
        # Deleting model 'Chunk'
        db.delete_table('hansard_chunk')
    
    
    models = {
        'hansard.chunk': {
            'Meta': {'object_name': 'Chunk'},
            'content': ('django.db.models.fields.TextField', [], {}),
            'date': ('django.db.models.fields.DateField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'page': ('django.db.models.fields.IntegerField', [], {}),
            'session': ('django.db.models.fields.CharField', [], {'max_length': '2'}),
            'source': ('django.db.models.fields.CharField', [], {'max_length': '500'}),
            'speaker': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'text_counter': ('django.db.models.fields.IntegerField', [], {}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '20'})
        }
    }
    
    complete_apps = ['hansard']

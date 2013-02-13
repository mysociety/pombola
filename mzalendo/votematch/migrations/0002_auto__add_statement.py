# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):
    
    def forwards(self, orm):
        
        # Adding model 'Statement'
        db.create_table('votematch_statement', (
            ('text', self.gf('django.db.models.fields.TextField')()),
            ('quiz', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['votematch.Quiz'])),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('modified', self.gf('model_utils.fields.AutoLastModifiedField')(default=datetime.datetime.now)),
            ('created', self.gf('model_utils.fields.AutoCreatedField')(default=datetime.datetime.now)),
        ))
        db.send_create_signal('votematch', ['Statement'])
    
    
    def backwards(self, orm):
        
        # Deleting model 'Statement'
        db.delete_table('votematch_statement')
    
    
    models = {
        'votematch.quiz': {
            'Meta': {'object_name': 'Quiz'},
            'created': ('model_utils.fields.AutoCreatedField', [], {'default': 'datetime.datetime.now'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified': ('model_utils.fields.AutoLastModifiedField', [], {'default': 'datetime.datetime.now'}),
            'name': ('django.db.models.fields.TextField', [], {'unique': 'True'}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '200', 'db_index': 'True'})
        },
        'votematch.statement': {
            'Meta': {'object_name': 'Statement'},
            'created': ('model_utils.fields.AutoCreatedField', [], {'default': 'datetime.datetime.now'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified': ('model_utils.fields.AutoLastModifiedField', [], {'default': 'datetime.datetime.now'}),
            'quiz': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['votematch.Quiz']"}),
            'text': ('django.db.models.fields.TextField', [], {})
        }
    }
    
    complete_apps = ['votematch']

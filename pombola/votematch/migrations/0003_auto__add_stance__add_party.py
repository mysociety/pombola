# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):
    
    def forwards(self, orm):
        
        # Adding model 'Stance'
        db.create_table('votematch_stance', (
            ('created', self.gf('model_utils.fields.AutoCreatedField')(default=datetime.datetime.now)),
            ('agreement', self.gf('django.db.models.fields.IntegerField')()),
            ('modified', self.gf('model_utils.fields.AutoLastModifiedField')(default=datetime.datetime.now)),
            ('statement', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['votematch.Statement'])),
            ('party', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['votematch.Party'])),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
        ))
        db.send_create_signal('votematch', ['Stance'])

        # Adding model 'Party'
        db.create_table('votematch_party', (
            ('name', self.gf('django.db.models.fields.TextField')()),
            ('created', self.gf('model_utils.fields.AutoCreatedField')(default=datetime.datetime.now)),
            ('modified', self.gf('model_utils.fields.AutoLastModifiedField')(default=datetime.datetime.now)),
            ('_summary_rendered', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('quiz', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['votematch.Quiz'])),
            ('summary', self.gf('markitup.fields.MarkupField')(no_rendered_field=True)),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
        ))
        db.send_create_signal('votematch', ['Party'])
    
    
    def backwards(self, orm):
        
        # Deleting model 'Stance'
        db.delete_table('votematch_stance')

        # Deleting model 'Party'
        db.delete_table('votematch_party')
    
    
    models = {
        'votematch.party': {
            'Meta': {'object_name': 'Party'},
            '_summary_rendered': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'created': ('model_utils.fields.AutoCreatedField', [], {'default': 'datetime.datetime.now'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified': ('model_utils.fields.AutoLastModifiedField', [], {'default': 'datetime.datetime.now'}),
            'name': ('django.db.models.fields.TextField', [], {}),
            'quiz': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['votematch.Quiz']"}),
            'summary': ('markitup.fields.MarkupField', [], {'no_rendered_field': 'True'})
        },
        'votematch.quiz': {
            'Meta': {'object_name': 'Quiz'},
            'created': ('model_utils.fields.AutoCreatedField', [], {'default': 'datetime.datetime.now'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified': ('model_utils.fields.AutoLastModifiedField', [], {'default': 'datetime.datetime.now'}),
            'name': ('django.db.models.fields.TextField', [], {'unique': 'True'}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '200', 'db_index': 'True'})
        },
        'votematch.stance': {
            'Meta': {'object_name': 'Stance'},
            'agreement': ('django.db.models.fields.IntegerField', [], {}),
            'created': ('model_utils.fields.AutoCreatedField', [], {'default': 'datetime.datetime.now'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified': ('model_utils.fields.AutoLastModifiedField', [], {'default': 'datetime.datetime.now'}),
            'party': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['votematch.Party']"}),
            'statement': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['votematch.Statement']"})
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

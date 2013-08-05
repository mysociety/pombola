# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):
    
    def forwards(self, orm):
        
        # Adding model 'Answer'
        db.create_table('votematch_answer', (
            ('submission', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['votematch.Submission'])),
            ('created', self.gf('model_utils.fields.AutoCreatedField')(default=datetime.datetime.now)),
            ('agreement', self.gf('django.db.models.fields.IntegerField')()),
            ('modified', self.gf('model_utils.fields.AutoLastModifiedField')(default=datetime.datetime.now)),
            ('statement', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['votematch.Statement'])),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
        ))
        db.send_create_signal('votematch', ['Answer'])

        # Adding model 'Submission'
        db.create_table('votematch_submission', (
            ('created', self.gf('model_utils.fields.AutoCreatedField')(default=datetime.datetime.now)),
            ('age', self.gf('django.db.models.fields.PositiveIntegerField')(null=True, blank=True)),
            ('modified', self.gf('model_utils.fields.AutoLastModifiedField')(default=datetime.datetime.now)),
            ('quiz', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['votematch.Quiz'])),
            ('token', self.gf('django.db.models.fields.TextField')(default='bc033d36', unique=True)),
            ('expected_result', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['votematch.Party'])),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
        ))
        db.send_create_signal('votematch', ['Submission'])
    
    
    def backwards(self, orm):
        
        # Deleting model 'Answer'
        db.delete_table('votematch_answer')

        # Deleting model 'Submission'
        db.delete_table('votematch_submission')
    
    
    models = {
        'votematch.answer': {
            'Meta': {'object_name': 'Answer'},
            'agreement': ('django.db.models.fields.IntegerField', [], {}),
            'created': ('model_utils.fields.AutoCreatedField', [], {'default': 'datetime.datetime.now'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified': ('model_utils.fields.AutoLastModifiedField', [], {'default': 'datetime.datetime.now'}),
            'statement': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['votematch.Statement']"}),
            'submission': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['votematch.Submission']"})
        },
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
        },
        'votematch.submission': {
            'Meta': {'object_name': 'Submission'},
            'age': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'created': ('model_utils.fields.AutoCreatedField', [], {'default': 'datetime.datetime.now'}),
            'expected_result': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['votematch.Party']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified': ('model_utils.fields.AutoLastModifiedField', [], {'default': 'datetime.datetime.now'}),
            'quiz': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['votematch.Quiz']"}),
            'token': ('django.db.models.fields.TextField', [], {'default': "'12e57036'", 'unique': 'True'})
        }
    }
    
    complete_apps = ['votematch']

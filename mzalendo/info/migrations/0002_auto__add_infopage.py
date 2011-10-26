# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):
    
    def forwards(self, orm):
        
        # Adding model 'InfoPage'
        db.create_table('info_infopage', (
            ('updated', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime(2011, 10, 4, 15, 29, 25, 799068), auto_now=True, blank=True)),
            ('title', self.gf('django.db.models.fields.CharField')(unique=True, max_length=300)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime(2011, 10, 4, 15, 29, 25, 797709), auto_now_add=True, blank=True)),
            ('slug', self.gf('django.db.models.fields.SlugField')(unique=True, max_length=50, db_index=True)),
            ('content', self.gf('markitup.fields.MarkupField')(no_rendered_field=True)),
            ('_content_rendered', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
        ))
        db.send_create_signal('info', ['InfoPage'])
    
    
    def backwards(self, orm):
        
        # Deleting model 'InfoPage'
        db.delete_table('info_infopage')
    
    
    models = {
        'info.infopage': {
            'Meta': {'object_name': 'InfoPage'},
            '_content_rendered': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'content': ('markitup.fields.MarkupField', [], {'no_rendered_field': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2011, 10, 4, 15, 29, 25, 797709)', 'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '50', 'db_index': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '300'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2011, 10, 4, 15, 29, 25, 799068)', 'auto_now': 'True', 'blank': 'True'})
        }
    }
    
    complete_apps = ['info']

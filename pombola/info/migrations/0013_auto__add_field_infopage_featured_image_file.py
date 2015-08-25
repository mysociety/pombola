# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    depends_on = (
        ('file_archive', '0001_initial'),
    )

    def forwards(self, orm):
        # Adding field 'InfoPage.featured_image_file'
        db.add_column(u'info_infopage', 'featured_image_file',
                      self.gf('django.db.models.fields.related.ForeignKey')(to=orm['file_archive.File'], null=True, blank=True),
                      keep_default=False)


    def backwards(self, orm):
        # Deleting field 'InfoPage.featured_image_file'
        db.delete_column(u'info_infopage', 'featured_image_file_id')


    models = {
        u'file_archive.file': {
            'Meta': {'object_name': 'File'},
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'auto_now_add': 'True', 'blank': 'True'}),
            'file': ('django.db.models.fields.files.FileField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '50'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'auto_now': 'True', 'blank': 'True'})
        },
        u'info.category': {
            'Meta': {'object_name': 'Category'},
            u'_summary_rendered': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'auto_now_add': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '300'}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '50'}),
            'summary': ('markitup.fields.MarkupField', [], {u'no_rendered_field': 'True', 'blank': 'True'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'auto_now': 'True', 'blank': 'True'})
        },
        u'info.infopage': {
            'Meta': {'ordering': "['title']", 'object_name': 'InfoPage'},
            u'_markdown_content_rendered': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'categories': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'entries'", 'blank': 'True', 'to': u"orm['info.Category']"}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'auto_now_add': 'True', 'blank': 'True'}),
            'featured_image_file': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['file_archive.File']", 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'kind': ('django.db.models.fields.CharField', [], {'default': "'page'", 'max_length': '10'}),
            'markdown_content': ('markitup.fields.MarkupField', [], {'default': "''", u'no_rendered_field': 'True', 'blank': 'True'}),
            'publication_date': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'raw_content': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '50'}),
            'tags': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'entries'", 'blank': 'True', 'to': u"orm['info.Tag']"}),
            'title': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '300'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'auto_now': 'True', 'blank': 'True'}),
            'use_raw': ('django.db.models.fields.BooleanField', [], {'default': 'False'})
        },
        u'info.tag': {
            'Meta': {'ordering': "('name',)", 'object_name': 'Tag'},
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'auto_now_add': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '300'}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '50'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'auto_now': 'True', 'blank': 'True'})
        },
        u'info.viewcount': {
            'Meta': {'unique_together': "(('date', 'page'),)", 'object_name': 'ViewCount'},
            'count': ('django.db.models.fields.IntegerField', [], {}),
            'date': ('django.db.models.fields.DateField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'page': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['info.InfoPage']"})
        }
    }

    complete_apps = ['info']

# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'BudgetSession'
        db.create_table(u'budgets_budgetsession', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now, auto_now_add=True, blank=True)),
            ('updated', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now, auto_now=True, blank=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=150)),
            ('date_start', self.gf('django_date_extensions.fields.ApproximateDateField')(max_length=10, blank=True)),
            ('date_end', self.gf('django_date_extensions.fields.ApproximateDateField')(max_length=10, blank=True)),
        ))
        db.send_create_signal(u'budgets', ['BudgetSession'])

        # Adding model 'Budget'
        db.create_table(u'budgets_budget', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now, auto_now_add=True, blank=True)),
            ('updated', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now, auto_now=True, blank=True)),
            ('content_type', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['contenttypes.ContentType'])),
            ('object_id', self.gf('django.db.models.fields.PositiveIntegerField')()),
            ('organisation', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['core.Organisation'], null=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=150)),
            ('budget_session', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['budgets.BudgetSession'], null=True)),
            ('currency', self.gf('django.db.models.fields.CharField')(max_length=3)),
            ('value', self.gf('django.db.models.fields.IntegerField')()),
            ('source_url', self.gf('django.db.models.fields.URLField')(max_length=200, blank=True)),
            ('source_name', self.gf('django.db.models.fields.CharField')(max_length=200, blank=True)),
        ))
        db.send_create_signal(u'budgets', ['Budget'])

        # Adding unique constraint on 'Budget', fields ['content_type', 'object_id', 'name', 'budget_session']
        db.create_unique(u'budgets_budget', ['content_type_id', 'object_id', 'name', 'budget_session_id'])


    def backwards(self, orm):
        # Removing unique constraint on 'Budget', fields ['content_type', 'object_id', 'name', 'budget_session']
        db.delete_unique(u'budgets_budget', ['content_type_id', 'object_id', 'name', 'budget_session_id'])

        # Deleting model 'BudgetSession'
        db.delete_table(u'budgets_budgetsession')

        # Deleting model 'Budget'
        db.delete_table(u'budgets_budget')


    models = {
        u'budgets.budget': {
            'Meta': {'ordering': "('-budget_session__date_start', 'name')", 'unique_together': "(('content_type', 'object_id', 'name', 'budget_session'),)", 'object_name': 'Budget'},
            'budget_session': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['budgets.BudgetSession']", 'null': 'True'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']"}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'auto_now_add': 'True', 'blank': 'True'}),
            'currency': ('django.db.models.fields.CharField', [], {'max_length': '3'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '150'}),
            'object_id': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'organisation': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['core.Organisation']", 'null': 'True'}),
            'source_name': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'source_url': ('django.db.models.fields.URLField', [], {'max_length': '200', 'blank': 'True'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'auto_now': 'True', 'blank': 'True'}),
            'value': ('django.db.models.fields.IntegerField', [], {})
        },
        u'budgets.budgetsession': {
            'Meta': {'ordering': "('-date_start', 'name')", 'object_name': 'BudgetSession'},
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'auto_now_add': 'True', 'blank': 'True'}),
            'date_end': ('django_date_extensions.fields.ApproximateDateField', [], {'max_length': '10', 'blank': 'True'}),
            'date_start': ('django_date_extensions.fields.ApproximateDateField', [], {'max_length': '10', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '150'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'auto_now': 'True', 'blank': 'True'})
        },
        u'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        u'core.organisation': {
            'Meta': {'ordering': "['slug']", 'object_name': 'Organisation'},
            '_summary_rendered': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'ended': ('django_date_extensions.fields.ApproximateDateField', [], {'max_length': '10', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'kind': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['core.OrganisationKind']"}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '200'}),
            'started': ('django_date_extensions.fields.ApproximateDateField', [], {'max_length': '10', 'blank': 'True'}),
            'summary': ('markitup.fields.MarkupField', [], {'default': "''", 'no_rendered_field': 'True', 'blank': 'True'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        },
        u'core.organisationkind': {
            'Meta': {'ordering': "['slug']", 'object_name': 'OrganisationKind'},
            '_summary_rendered': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '200'}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '200'}),
            'summary': ('markitup.fields.MarkupField', [], {'default': "''", 'no_rendered_field': 'True', 'blank': 'True'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        }
    }

    complete_apps = ['budgets']
# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):

        # Renaming column for 'Budget.organisation' to match new field type.
        db.rename_column(u'budgets_budget', 'organisation_id', 'organisation')
        # Changing field 'Budget.organisation'
        db.alter_column(u'budgets_budget', 'organisation', self.gf('django.db.models.fields.CharField')(default='Funding Body', max_length=150))
        # Removing index on 'Budget', fields ['organisation']
        db.delete_index(u'budgets_budget', ['organisation_id'])


    def backwards(self, orm):
        # Adding index on 'Budget', fields ['organisation']
        db.create_index(u'budgets_budget', ['organisation_id'])


        # Renaming column for 'Budget.organisation' to match new field type.
        db.rename_column(u'budgets_budget', 'organisation', 'organisation_id')
        # Changing field 'Budget.organisation'
        db.alter_column(u'budgets_budget', 'organisation_id', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['core.Organisation'], null=True))

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
            'organisation': ('django.db.models.fields.CharField', [], {'max_length': '150'}),
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
        }
    }

    complete_apps = ['budgets']
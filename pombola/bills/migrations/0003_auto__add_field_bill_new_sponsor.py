# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):
    depends_on = (
        ('core', '0063_migrate_core_models_to_popolo'),
    )

    def forwards(self, orm):
        # Adding field 'Bill.new_sponsor'
        db.add_column(u'bills_bill', 'new_sponsor',
                      self.gf('django.db.models.fields.related.ForeignKey')(related_name='bills_sponsored', null=True, to=orm['core.PopoloPerson']),
                      keep_default=False)


    def backwards(self, orm):
        # Deleting field 'Bill.new_sponsor'
        db.delete_column(u'bills_bill', 'new_sponsor_id')


    models = {
        u'bills.bill': {
            'Meta': {'ordering': "('date',)", 'object_name': 'Bill'},
            'act_source_url': ('django.db.models.fields.URLField', [], {'max_length': '200', 'unique': 'True', 'null': 'True', 'blank': 'True'}),
            'act_title': ('django.db.models.fields.CharField', [], {'max_length': '256', 'null': 'True', 'blank': 'True'}),
            'date': ('django.db.models.fields.DateField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'new_sponsor': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'bills_sponsored'", 'null': 'True', 'to': u"orm['core.PopoloPerson']"}),
            'parliamentary_session': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['core.ParliamentarySession']"}),
            'source_url': ('django.db.models.fields.URLField', [], {'unique': 'True', 'max_length': '200'}),
            'sponsor': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'old_bills_sponsored'", 'to': u"orm['core.Person']"}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '256'})
        },
        u'core.organisationkind': {
            'Meta': {'ordering': "['slug']", 'object_name': 'OrganisationKind'},
            u'_summary_rendered': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '200'}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '200'}),
            'summary': ('markitup.fields.MarkupField', [], {'default': "''", u'no_rendered_field': 'True', 'blank': 'True'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        },
        u'core.parliamentarysession': {
            'Meta': {'ordering': "['start_date']", 'object_name': 'ParliamentarySession'},
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'end_date': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'house': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['core.PopoloOrganization']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'mapit_generation': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '200'}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '200'}),
            'start_date': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        },
        u'core.person': {
            'Meta': {'ordering': "['sort_name']", 'object_name': 'Person'},
            u'_biography_rendered': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            u'_summary_rendered': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'additional_name': ('django.db.models.fields.CharField', [], {'max_length': '300', 'blank': 'True'}),
            'biography': ('markitup.fields.MarkupField', [], {'default': "''", u'no_rendered_field': 'True', 'blank': 'True'}),
            'can_be_featured': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'date_of_birth': ('django_date_extensions.fields.ApproximateDateField', [], {'max_length': '10', 'blank': 'True'}),
            'date_of_death': ('django_date_extensions.fields.ApproximateDateField', [], {'max_length': '10', 'blank': 'True'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'family_name': ('django.db.models.fields.CharField', [], {'max_length': '300', 'blank': 'True'}),
            'gender': ('django.db.models.fields.CharField', [], {'max_length': '20', 'blank': 'True'}),
            'given_name': ('django.db.models.fields.CharField', [], {'max_length': '300', 'blank': 'True'}),
            'hidden': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'honorific_prefix': ('django.db.models.fields.CharField', [], {'max_length': '300', 'blank': 'True'}),
            'honorific_suffix': ('django.db.models.fields.CharField', [], {'max_length': '300', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'legal_name': ('django.db.models.fields.CharField', [], {'max_length': '300'}),
            'national_identity': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '200'}),
            'sort_name': ('django.db.models.fields.CharField', [], {'max_length': '300', 'blank': 'True'}),
            'summary': ('markitup.fields.MarkupField', [], {'default': "''", u'no_rendered_field': 'True', 'blank': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        },
        u'core.popoloorganization': {
            'Meta': {'object_name': 'PopoloOrganization', '_ormbases': [u'popolo.Organization']},
            u'_summary_rendered': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'kind': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['core.OrganisationKind']"}),
            u'organization_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['popolo.Organization']", 'unique': 'True', 'primary_key': 'True'}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '200'}),
            'summary': ('markitup.fields.MarkupField', [], {'default': "''", u'no_rendered_field': 'True', 'blank': 'True'})
        },
        u'core.popoloperson': {
            'Meta': {'object_name': 'PopoloPerson', '_ormbases': [u'popolo.Person']},
            'can_be_featured': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'hidden': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            u'person_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['popolo.Person']", 'unique': 'True', 'primary_key': 'True'}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '200'})
        },
        u'popolo.organization': {
            'Meta': {'object_name': 'Organization'},
            'classification': ('django.db.models.fields.CharField', [], {'max_length': '4000', 'blank': 'True'}),
            'created_at': ('model_utils.fields.AutoCreatedField', [], {'default': 'datetime.datetime.now'}),
            'dissolution_date': ('django.db.models.fields.CharField', [], {'max_length': '10', 'blank': 'True'}),
            'end_date': ('django.db.models.fields.CharField', [], {'max_length': '10', 'null': 'True', 'blank': 'True'}),
            'founding_date': ('django.db.models.fields.CharField', [], {'max_length': '10', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '4000'}),
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'children'", 'null': 'True', 'to': u"orm['popolo.Organization']"}),
            'start_date': ('django.db.models.fields.CharField', [], {'max_length': '10', 'null': 'True', 'blank': 'True'}),
            'updated_at': ('model_utils.fields.AutoLastModifiedField', [], {'default': 'datetime.datetime.now'})
        },
        u'popolo.person': {
            'Meta': {'object_name': 'Person'},
            'additional_name': ('django.db.models.fields.CharField', [], {'max_length': '4000', 'blank': 'True'}),
            'biography': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'birth_date': ('django.db.models.fields.CharField', [], {'max_length': '10', 'blank': 'True'}),
            'created_at': ('model_utils.fields.AutoCreatedField', [], {'default': 'datetime.datetime.now'}),
            'death_date': ('django.db.models.fields.CharField', [], {'max_length': '10', 'blank': 'True'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'null': 'True', 'blank': 'True'}),
            'end_date': ('django.db.models.fields.CharField', [], {'max_length': '10', 'null': 'True', 'blank': 'True'}),
            'family_name': ('django.db.models.fields.CharField', [], {'max_length': '4000', 'blank': 'True'}),
            'gender': ('django.db.models.fields.CharField', [], {'max_length': '128', 'blank': 'True'}),
            'given_name': ('django.db.models.fields.CharField', [], {'max_length': '4000', 'blank': 'True'}),
            'honorific_prefix': ('django.db.models.fields.CharField', [], {'max_length': '128', 'blank': 'True'}),
            'honorific_suffix': ('django.db.models.fields.CharField', [], {'max_length': '128', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'image': ('django.db.models.fields.URLField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '4000'}),
            'patronymic_name': ('django.db.models.fields.CharField', [], {'max_length': '4000', 'blank': 'True'}),
            'sort_name': ('django.db.models.fields.CharField', [], {'max_length': '4000', 'blank': 'True'}),
            'start_date': ('django.db.models.fields.CharField', [], {'max_length': '10', 'null': 'True', 'blank': 'True'}),
            'summary': ('django.db.models.fields.CharField', [], {'max_length': '4000', 'blank': 'True'}),
            'updated_at': ('model_utils.fields.AutoLastModifiedField', [], {'default': 'datetime.datetime.now'})
        }
    }

    complete_apps = ['bills']

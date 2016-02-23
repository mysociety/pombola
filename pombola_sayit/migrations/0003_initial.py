# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    depends_on = (
        ('core', '0001_initial'),
        ('speeches', '0054__rename_popolospeaker'),
    )

    def forwards(self, orm):
        # Adding model 'PombolaSayItJoin'
        db.create_table(u'pombola_sayit_pombolasayitjoin', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('pombola_person', self.gf('django.db.models.fields.related.OneToOneField')(related_name='sayit_link', unique=True, to=orm['core.Person'])),
            ('sayit_speaker', self.gf('django.db.models.fields.related.OneToOneField')(related_name='pombola_link', unique=True, to=orm['speeches.Speaker'])),
        ))
        db.send_create_signal(u'pombola_sayit', ['PombolaSayItJoin'])


    def backwards(self, orm):
        # Deleting model 'PombolaSayItJoin'
        db.delete_table(u'pombola_sayit_pombolasayitjoin')


    models = {
        u'auth.group': {
            'Meta': {'object_name': 'Group'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        u'auth.permission': {
            'Meta': {'ordering': "(u'content_type__app_label', u'content_type__model', u'codename')", 'unique_together': "((u'content_type', u'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        u'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "u'user_set'", 'blank': 'True', 'to': u"orm['auth.Group']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "u'user_set'", 'blank': 'True', 'to': u"orm['auth.Permission']"}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        u'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
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
            'speaker': ('django.db.models.fields.related.OneToOneField', [], {'blank': 'True', 'related_name': "'pombola_person'", 'unique': 'True', 'null': 'True', 'to': u"orm['speeches.Speaker']"}),
            'summary': ('markitup.fields.MarkupField', [], {'default': "''", u'no_rendered_field': 'True', 'blank': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        },
        u'instances.instance': {
            'Meta': {'object_name': 'Instance'},
            'created_by': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'created_instances'", 'null': 'True', 'to': u"orm['auth.User']"}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'label': ('instances.fields.DNSLabelField', [], {'unique': 'True', 'max_length': '63', 'db_index': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'users': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'instances'", 'blank': 'True', 'to': u"orm['auth.User']"})
        },
        u'pombola_sayit.pombolasayitjoin': {
            'Meta': {'object_name': 'PombolaSayItJoin'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'pombola_person': ('django.db.models.fields.related.OneToOneField', [], {'related_name': "'sayit_link'", 'unique': 'True', 'to': u"orm['core.Person']"}),
            'sayit_speaker': ('django.db.models.fields.related.OneToOneField', [], {'related_name': "'pombola_link'", 'unique': 'True', 'to': u"orm['speeches.Speaker']"})
        },
        u'popolo.person': {
            'Meta': {'object_name': 'Person'},
            'additional_name': ('django.db.models.fields.CharField', [], {'max_length': '128', 'blank': 'True'}),
            'biography': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'birth_date': ('django.db.models.fields.CharField', [], {'max_length': '10', 'blank': 'True'}),
            'created_at': ('model_utils.fields.AutoCreatedField', [], {'default': 'datetime.datetime.now'}),
            'death_date': ('django.db.models.fields.CharField', [], {'max_length': '10', 'blank': 'True'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'null': 'True', 'blank': 'True'}),
            'end_date': ('django.db.models.fields.CharField', [], {'max_length': '10', 'null': 'True', 'blank': 'True'}),
            'family_name': ('django.db.models.fields.CharField', [], {'max_length': '128', 'blank': 'True'}),
            'gender': ('django.db.models.fields.CharField', [], {'max_length': '128', 'blank': 'True'}),
            'given_name': ('django.db.models.fields.CharField', [], {'max_length': '128', 'blank': 'True'}),
            'honorific_prefix': ('django.db.models.fields.CharField', [], {'max_length': '128', 'blank': 'True'}),
            'honorific_suffix': ('django.db.models.fields.CharField', [], {'max_length': '128', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'image': ('django.db.models.fields.URLField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'patronymic_name': ('django.db.models.fields.CharField', [], {'max_length': '128', 'blank': 'True'}),
            'sort_name': ('django.db.models.fields.CharField', [], {'max_length': '128', 'blank': 'True'}),
            'start_date': ('django.db.models.fields.CharField', [], {'max_length': '10', 'null': 'True', 'blank': 'True'}),
            'summary': ('django.db.models.fields.CharField', [], {'max_length': '512', 'blank': 'True'}),
            'updated_at': ('model_utils.fields.AutoLastModifiedField', [], {'default': 'datetime.datetime.now'})
        },
        u'speeches.speaker': {
            'Meta': {'unique_together': "(('instance', 'slug'),)", 'object_name': 'Speaker', '_ormbases': [u'popolo.Person']},
            'image_cache': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'instance': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['instances.Instance']"}),
            u'person_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['popolo.Person']", 'unique': 'True', 'primary_key': 'True'}),
            'slug': (u'sluggable.fields.SluggableField', [], {u'unique_with': "('instance',)", 'max_length': '50', u'populate_from': "'name'"})
        }
    }

    complete_apps = ['pombola_sayit']

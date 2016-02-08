# -*- coding: utf-8 -*-
import re

from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import DataMigration
from django.db import models

class Migration(DataMigration):

    depends_on = (
        ('speeches', '0056_auto__add_field_speaker_image_cache'),
    )

    def forwards(self, orm):
        Identifier = orm['popolo.Identifier']
        popolo_person_ct = orm['contenttypes.ContentType'].objects.get(
            app_label='popolo', model='person'
        )
        for speaker in orm['speeches.Speaker'].objects.all():
            identifiers = Identifier.objects.filter(
                content_type_id=popolo_person_ct.id,
                object_id=speaker.person_ptr.id,
            )
            try:
                i = identifiers.get(scheme='PopIt ID')
                m = re.search(r'core_person:(\d+)', i.identifier)
                if not m:
                    print "Ignoring malformed PopIt ID: {0}".format(i.identifier)
                    continue
                pombola_person_id = m.group(1)
                try:
                    pombola_person = orm['core.Person'].objects.get(
                        pk=pombola_person_id
                    )
                except orm['core.Person'].DoesNotExist:
                    msg = "Couldn't find a Pombola Person with ID {0}"
                    print msg.format(pombola_person_id)
                    continue
                orm.PombolaSayItJoin.objects.create(
                    pombola_person=pombola_person,
                    sayit_speaker=speaker,
                )
            except Identifier.DoesNotExist:
                # Lots of people don't have any identifiers linking
                # them to Pombola people.  They are names that
                # couldn't be matched, but for whom a speaker was
                # created.
                pass

    def backwards(self, orm):
        "Write your backwards methods here."

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
        u'popolo.contactdetail': {
            'Meta': {'object_name': 'ContactDetail'},
            'contact_type': ('django.db.models.fields.CharField', [], {'max_length': '12'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']"}),
            'created_at': ('model_utils.fields.AutoCreatedField', [], {'default': 'datetime.datetime.now'}),
            'end_date': ('django.db.models.fields.CharField', [], {'max_length': '10', 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'label': ('django.db.models.fields.CharField', [], {'max_length': '128', 'blank': 'True'}),
            'note': ('django.db.models.fields.CharField', [], {'max_length': '128', 'blank': 'True'}),
            'object_id': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'start_date': ('django.db.models.fields.CharField', [], {'max_length': '10', 'null': 'True', 'blank': 'True'}),
            'updated_at': ('model_utils.fields.AutoLastModifiedField', [], {'default': 'datetime.datetime.now'}),
            'value': ('django.db.models.fields.CharField', [], {'max_length': '128'})
        },
        u'popolo.identifier': {
            'Meta': {'object_name': 'Identifier'},
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'identifier': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'object_id': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'scheme': ('django.db.models.fields.CharField', [], {'max_length': '128', 'blank': 'True'})
        },
        u'popolo.link': {
            'Meta': {'object_name': 'Link'},
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'note': ('django.db.models.fields.CharField', [], {'max_length': '128', 'blank': 'True'}),
            'object_id': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'url': ('django.db.models.fields.URLField', [], {'max_length': '200'})
        },
        u'popolo.membership': {
            'Meta': {'object_name': 'Membership'},
            'created_at': ('model_utils.fields.AutoCreatedField', [], {'default': 'datetime.datetime.now'}),
            'end_date': ('django.db.models.fields.CharField', [], {'max_length': '10', 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'label': ('django.db.models.fields.CharField', [], {'max_length': '128', 'blank': 'True'}),
            'on_behalf_of': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'memberships_on_behalf_of'", 'null': 'True', 'to': u"orm['popolo.Organization']"}),
            'organization': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'memberships'", 'to': u"orm['popolo.Organization']"}),
            'person': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'memberships'", 'to': u"orm['popolo.Person']"}),
            'post': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'memberships'", 'null': 'True', 'to': u"orm['popolo.Post']"}),
            'role': ('django.db.models.fields.CharField', [], {'max_length': '128', 'blank': 'True'}),
            'start_date': ('django.db.models.fields.CharField', [], {'max_length': '10', 'null': 'True', 'blank': 'True'}),
            'updated_at': ('model_utils.fields.AutoLastModifiedField', [], {'default': 'datetime.datetime.now'})
        },
        u'popolo.organization': {
            'Meta': {'object_name': 'Organization'},
            'classification': ('django.db.models.fields.CharField', [], {'max_length': '128', 'blank': 'True'}),
            'created_at': ('model_utils.fields.AutoCreatedField', [], {'default': 'datetime.datetime.now'}),
            'dissolution_date': ('django.db.models.fields.CharField', [], {'max_length': '10', 'blank': 'True'}),
            'end_date': ('django.db.models.fields.CharField', [], {'max_length': '10', 'null': 'True', 'blank': 'True'}),
            'founding_date': ('django.db.models.fields.CharField', [], {'max_length': '10', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'children'", 'null': 'True', 'to': u"orm['popolo.Organization']"}),
            'start_date': ('django.db.models.fields.CharField', [], {'max_length': '10', 'null': 'True', 'blank': 'True'}),
            'updated_at': ('model_utils.fields.AutoLastModifiedField', [], {'default': 'datetime.datetime.now'})
        },
        u'popolo.othername': {
            'Meta': {'object_name': 'OtherName'},
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']"}),
            'end_date': ('django.db.models.fields.CharField', [], {'max_length': '10', 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'note': ('django.db.models.fields.CharField', [], {'max_length': '256', 'blank': 'True'}),
            'object_id': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'start_date': ('django.db.models.fields.CharField', [], {'max_length': '10', 'null': 'True', 'blank': 'True'})
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
        u'popolo.post': {
            'Meta': {'object_name': 'Post'},
            'created_at': ('model_utils.fields.AutoCreatedField', [], {'default': 'datetime.datetime.now'}),
            'end_date': ('django.db.models.fields.CharField', [], {'max_length': '10', 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'label': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'organization': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'posts'", 'to': u"orm['popolo.Organization']"}),
            'role': ('django.db.models.fields.CharField', [], {'max_length': '128', 'blank': 'True'}),
            'start_date': ('django.db.models.fields.CharField', [], {'max_length': '10', 'null': 'True', 'blank': 'True'}),
            'updated_at': ('model_utils.fields.AutoLastModifiedField', [], {'default': 'datetime.datetime.now'})
        },
        u'popolo.source': {
            'Meta': {'object_name': 'Source'},
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'note': ('django.db.models.fields.CharField', [], {'max_length': '128', 'blank': 'True'}),
            'object_id': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'url': ('django.db.models.fields.URLField', [], {'max_length': '200'})
        },
        u'speeches.speaker': {
            'Meta': {'unique_together': "(('instance', 'slug'),)", 'object_name': 'Speaker', '_ormbases': [u'popolo.Person']},
            'image_cache': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'instance': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['instances.Instance']"}),
            u'person_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['popolo.Person']", 'unique': 'True', 'primary_key': 'True'}),
            'slug': (u'sluggable.fields.SluggableField', [], {u'unique_with': "('instance',)", 'max_length': '50', u'populate_from': "'name'"})
        }
    }

    complete_apps = ['popolo', 'pombola_sayit']
    symmetrical = True

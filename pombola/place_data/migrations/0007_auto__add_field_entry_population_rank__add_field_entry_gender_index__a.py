# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding field 'Entry.population_rank'
        db.add_column('place_data_entry', 'population_rank', self.gf('django.db.models.fields.PositiveIntegerField')(null=True), keep_default=False)

        # Adding field 'Entry.gender_index'
        db.add_column('place_data_entry', 'gender_index', self.gf('django.db.models.fields.DecimalField')(null=True, max_digits=7, decimal_places=6), keep_default=False)

        # Adding field 'Entry.gender_index_rank'
        db.add_column('place_data_entry', 'gender_index_rank', self.gf('django.db.models.fields.PositiveIntegerField')(null=True), keep_default=False)

        # Adding field 'Entry.average_household_size'
        db.add_column('place_data_entry', 'average_household_size', self.gf('django.db.models.fields.DecimalField')(null=True, max_digits=5, decimal_places=3), keep_default=False)

        # Adding field 'Entry.household_size_rank'
        db.add_column('place_data_entry', 'household_size_rank', self.gf('django.db.models.fields.PositiveIntegerField')(null=True), keep_default=False)

        # Adding field 'Entry.area_rank'
        db.add_column('place_data_entry', 'area_rank', self.gf('django.db.models.fields.PositiveIntegerField')(null=True), keep_default=False)

        # Adding field 'Entry.population_density'
        db.add_column('place_data_entry', 'population_density', self.gf('django.db.models.fields.DecimalField')(null=True, max_digits=9, decimal_places=2), keep_default=False)

        # Adding field 'Entry.population_density_rank'
        db.add_column('place_data_entry', 'population_density_rank', self.gf('django.db.models.fields.PositiveIntegerField')(null=True), keep_default=False)

        # Adding field 'Entry.registered_voters_total'
        db.add_column('place_data_entry', 'registered_voters_total', self.gf('django.db.models.fields.PositiveIntegerField')(null=True), keep_default=False)

        # Adding field 'Entry.registered_voters_proportion'
        db.add_column('place_data_entry', 'registered_voters_proportion', self.gf('django.db.models.fields.DecimalField')(null=True, max_digits=4, decimal_places=3), keep_default=False)

        # Adding field 'Entry.registered_voters_proportion_rank'
        db.add_column('place_data_entry', 'registered_voters_proportion_rank', self.gf('django.db.models.fields.PositiveIntegerField')(null=True), keep_default=False)

        # Adding field 'Entry.youth_voters_proportion'
        db.add_column('place_data_entry', 'youth_voters_proportion', self.gf('django.db.models.fields.DecimalField')(null=True, max_digits=4, decimal_places=3), keep_default=False)

        # Adding field 'Entry.youth_voters_proportion_rank'
        db.add_column('place_data_entry', 'youth_voters_proportion_rank', self.gf('django.db.models.fields.PositiveIntegerField')(null=True), keep_default=False)


    def backwards(self, orm):
        
        # Deleting field 'Entry.population_rank'
        db.delete_column('place_data_entry', 'population_rank')

        # Deleting field 'Entry.gender_index'
        db.delete_column('place_data_entry', 'gender_index')

        # Deleting field 'Entry.gender_index_rank'
        db.delete_column('place_data_entry', 'gender_index_rank')

        # Deleting field 'Entry.average_household_size'
        db.delete_column('place_data_entry', 'average_household_size')

        # Deleting field 'Entry.household_size_rank'
        db.delete_column('place_data_entry', 'household_size_rank')

        # Deleting field 'Entry.area_rank'
        db.delete_column('place_data_entry', 'area_rank')

        # Deleting field 'Entry.population_density'
        db.delete_column('place_data_entry', 'population_density')

        # Deleting field 'Entry.population_density_rank'
        db.delete_column('place_data_entry', 'population_density_rank')

        # Deleting field 'Entry.registered_voters_total'
        db.delete_column('place_data_entry', 'registered_voters_total')

        # Deleting field 'Entry.registered_voters_proportion'
        db.delete_column('place_data_entry', 'registered_voters_proportion')

        # Deleting field 'Entry.registered_voters_proportion_rank'
        db.delete_column('place_data_entry', 'registered_voters_proportion_rank')

        # Deleting field 'Entry.youth_voters_proportion'
        db.delete_column('place_data_entry', 'youth_voters_proportion')

        # Deleting field 'Entry.youth_voters_proportion_rank'
        db.delete_column('place_data_entry', 'youth_voters_proportion_rank')


    models = {
        'auth.group': {
            'Meta': {'object_name': 'Group'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        'auth.permission': {
            'Meta': {'ordering': "('content_type__app_label', 'content_type__model', 'codename')", 'unique_together': "(('content_type', 'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        'comments2.comment': {
            'Meta': {'ordering': "('-submit_date',)", 'object_name': 'Comment'},
            'comment': ('django.db.models.fields.TextField', [], {'max_length': '3000'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'content_type_set_for_comment'", 'to': "orm['contenttypes.ContentType']"}),
            'flag_count': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'ip_address': ('django.db.models.fields.IPAddressField', [], {'max_length': '15', 'null': 'True', 'blank': 'True'}),
            'object_id': ('django.db.models.fields.IntegerField', [], {}),
            'status': ('django.db.models.fields.CharField', [], {'default': "'unmoderated'", 'max_length': '20'}),
            'submit_date': ('django.db.models.fields.DateTimeField', [], {'default': 'None'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '300'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'comment_comments'", 'to': "orm['auth.User']"})
        },
        'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'core.contact': {
            'Meta': {'ordering': "['content_type', 'object_id', 'kind']", 'object_name': 'Contact'},
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2012, 2, 16, 15, 12, 15, 614017)', 'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'kind': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.ContactKind']"}),
            'note': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'object_id': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'source': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '500', 'blank': 'True'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2012, 2, 16, 15, 12, 15, 614051)', 'auto_now': 'True', 'blank': 'True'}),
            'value': ('django.db.models.fields.TextField', [], {})
        },
        'core.contactkind': {
            'Meta': {'ordering': "['slug']", 'object_name': 'ContactKind'},
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2012, 2, 16, 15, 12, 15, 614017)', 'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '200'}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '200', 'db_index': 'True'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2012, 2, 16, 15, 12, 15, 614051)', 'auto_now': 'True', 'blank': 'True'})
        },
        'core.organisation': {
            'Meta': {'ordering': "['slug']", 'object_name': 'Organisation'},
            '_summary_rendered': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2012, 2, 16, 15, 12, 15, 614017)', 'auto_now_add': 'True', 'blank': 'True'}),
            'ended': ('django_date_extensions.fields.ApproximateDateField', [], {'max_length': '10', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'kind': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.OrganisationKind']"}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'original_id': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '200', 'db_index': 'True'}),
            'started': ('django_date_extensions.fields.ApproximateDateField', [], {'max_length': '10', 'blank': 'True'}),
            'summary': ('markitup.fields.MarkupField', [], {'default': "''", 'no_rendered_field': 'True', 'blank': 'True'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2012, 2, 16, 15, 12, 15, 614051)', 'auto_now': 'True', 'blank': 'True'})
        },
        'core.organisationkind': {
            'Meta': {'ordering': "['slug']", 'object_name': 'OrganisationKind'},
            '_summary_rendered': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2012, 2, 16, 15, 12, 15, 614017)', 'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '200'}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '200', 'db_index': 'True'}),
            'summary': ('markitup.fields.MarkupField', [], {'default': "''", 'no_rendered_field': 'True', 'blank': 'True'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2012, 2, 16, 15, 12, 15, 614051)', 'auto_now': 'True', 'blank': 'True'})
        },
        'core.place': {
            'Meta': {'ordering': "['slug']", 'object_name': 'Place'},
            '_summary_rendered': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2012, 2, 16, 15, 12, 15, 614017)', 'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'kind': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.PlaceKind']"}),
            'location': ('django.contrib.gis.db.models.fields.PointField', [], {'null': 'True', 'blank': 'True'}),
            'mapit_id': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'organisation': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Organisation']", 'null': 'True', 'blank': 'True'}),
            'original_id': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'parent_place': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'child_places'", 'null': 'True', 'to': "orm['core.Place']"}),
            'shape_url': ('django.db.models.fields.URLField', [], {'max_length': '200', 'blank': 'True'}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '100', 'db_index': 'True'}),
            'summary': ('markitup.fields.MarkupField', [], {'default': "''", 'no_rendered_field': 'True', 'blank': 'True'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2012, 2, 16, 15, 12, 15, 614051)', 'auto_now': 'True', 'blank': 'True'})
        },
        'core.placekind': {
            'Meta': {'ordering': "['slug']", 'object_name': 'PlaceKind'},
            '_summary_rendered': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2012, 2, 16, 15, 12, 15, 614017)', 'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '200'}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '200', 'db_index': 'True'}),
            'summary': ('markitup.fields.MarkupField', [], {'default': "''", 'no_rendered_field': 'True', 'blank': 'True'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2012, 2, 16, 15, 12, 15, 614051)', 'auto_now': 'True', 'blank': 'True'})
        },
        'place_data.entry': {
            'Meta': {'object_name': 'Entry'},
            'area': ('django.db.models.fields.DecimalField', [], {'max_digits': '10', 'decimal_places': '2'}),
            'area_rank': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True'}),
            'average_household_size': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '5', 'decimal_places': '3'}),
            'gender_index': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '7', 'decimal_places': '6'}),
            'gender_index_rank': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True'}),
            'household_size_rank': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True'}),
            'households_total': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'place': ('django.db.models.fields.related.OneToOneField', [], {'related_name': "'placedata'", 'unique': 'True', 'to': "orm['core.Place']"}),
            'population_density': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '9', 'decimal_places': '2'}),
            'population_density_rank': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True'}),
            'population_female': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'population_male': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'population_rank': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True'}),
            'population_total': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'registered_voters_proportion': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '4', 'decimal_places': '3'}),
            'registered_voters_proportion_rank': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True'}),
            'registered_voters_total': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True'}),
            'youth_voters_proportion': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '4', 'decimal_places': '3'}),
            'youth_voters_proportion_rank': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True'})
        },
        'scorecards.category': {
            'Meta': {'ordering': "('name',)", 'object_name': 'Category'},
            '_description_rendered': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2012, 2, 16, 15, 12, 15, 612024)', 'auto_now_add': 'True', 'blank': 'True'}),
            'description': ('markitup.fields.MarkupField', [], {'no_rendered_field': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '200'}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '50', 'db_index': 'True'}),
            'synopsis': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2012, 2, 16, 15, 12, 15, 612058)', 'auto_now': 'True', 'blank': 'True'})
        },
        'scorecards.entry': {
            'Meta': {'ordering': "('-date', 'category')", 'unique_together': "(('content_type', 'object_id', 'category', 'date'),)", 'object_name': 'Entry'},
            '_equivalent_remark_rendered': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            '_extended_remark_rendered': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'category': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['scorecards.Category']"}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2012, 2, 16, 15, 12, 15, 612653)', 'auto_now_add': 'True', 'blank': 'True'}),
            'date': ('django.db.models.fields.DateField', [], {}),
            'disabled': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'disabled_comment': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '300', 'blank': 'True'}),
            'equivalent_remark': ('markitup.fields.MarkupField', [], {'max_length': '400', 'no_rendered_field': 'True', 'blank': 'True'}),
            'extended_remark': ('markitup.fields.MarkupField', [], {'max_length': '1000', 'no_rendered_field': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'object_id': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'remark': ('django.db.models.fields.CharField', [], {'max_length': '150'}),
            'score': ('django.db.models.fields.IntegerField', [], {}),
            'source_name': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'source_url': ('django.db.models.fields.URLField', [], {'max_length': '200', 'blank': 'True'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2012, 2, 16, 15, 12, 15, 612682)', 'auto_now': 'True', 'blank': 'True'})
        }
    }

    complete_apps = ['place_data']

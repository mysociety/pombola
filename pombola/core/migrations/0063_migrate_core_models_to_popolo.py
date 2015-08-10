# -*- coding: utf-8 -*-
from south.v2 import DataMigration
from django.contrib.contenttypes.generic import GenericRelation
from django.core.validators import URLValidator
from django.core.exceptions import ValidationError

class Migration(DataMigration):

    def forwards(self, orm):
        self._migrate_place_identifiers(orm)
        self._migrate_person_forwards(orm)
        self._migrate_organisation_forwards(orm)
        self._migrate_position_forwards(orm)

    def _is_url(self, url):
        try:
            URLValidator()(url)
        except ValidationError:
            return False
        else:
            return True

    def _migrate_place_identifiers(self, orm):
        GenericRelation(orm.Identifier).contribute_to_class(orm.Place, "core_identifier_set")

        for place in orm.Place.objects.all():
            self._migrate_identifiers(orm, place, place, 'place')

    def _migrate_organisation_forwards(self, orm):
        GenericRelation(orm.Contact).contribute_to_class(orm.Organisation, "contacts")
        GenericRelation(orm.Identifier).contribute_to_class(orm.Organisation, "core_identifier_set")

        for old_org in orm.Organisation.objects.all():
            new_org = orm.PopoloOrganization()

            new_org.name = old_org.name

            if old_org.started:
                new_org.founding_date = repr(old_org.started)
            if old_org.ended:
                new_org.dissolution_date = repr(old_org.ended)

            new_org.slug = old_org.slug
            new_org.kind = old_org.kind
            new_org.summary = old_org.summary

            new_org.created_at = old_org.created
            new_org.updated_at = old_org.updated

            new_org.save()

            for contact in old_org.contacts.all():
                self._migrate_contact(orm, contact, new_org, 'organization')

            self._add_old_identifier(orm, old_org, new_org, 'popoloorganization')
            self._migrate_identifiers(orm, old_org, new_org, 'popoloorganization')

    def _migrate_person_forwards(self, orm):
        GenericRelation(orm.Contact).contribute_to_class(orm.Person, "contacts")
        GenericRelation(orm['images.Image']).contribute_to_class(orm.Person, "images")
        GenericRelation(orm['images.Image']).contribute_to_class(orm.PopoloPerson, "images")
        GenericRelation(orm.Identifier).contribute_to_class(orm.Person, "core_identifier_set")

        popolo_person_content_type = orm['contenttypes.ContentType'].objects.get(
            app_label="core", model="popoloperson"
        )

        for old_person in orm.Person.objects.all():
            new_person = orm.PopoloPerson()

            new_person.honorific_prefix = old_person.title
            new_person.name = old_person.legal_name
            new_person.slug = old_person.slug
            new_person.gender = old_person.gender

            if old_person.date_of_birth:
                new_person.birth_date = repr(old_person.date_of_birth)
            if old_person.date_of_death:
                new_person.death_date = repr(old_person.date_of_death)

            new_person.summary = old_person.summary
            new_person.email = old_person.email
            new_person.hidden = old_person.hidden

            new_person.can_be_featured = old_person.can_be_featured
            new_person.biography = old_person.biography
            new_person.national_identity = old_person.national_identity
            new_person.family_name = old_person.family_name
            new_person.given_name = old_person.given_name
            new_person.additional_name = old_person.additional_name
            # honorific_prefix present in old core Person model but unused
            new_person.honorific_suffix = old_person.honorific_suffix
            new_person.sort_name = old_person.sort_name

            new_person.created_at = old_person.created
            new_person.updated_at = old_person.updated

            new_person.save()

            for contact in old_person.contacts.all():
                self._migrate_contact(orm, contact, new_person, 'person')

            for old_image in old_person.images.all():
                orm['images.Image'].objects.create(
                    content_type=popolo_person_content_type,
                    object_id=new_person.id,
                    image=old_image.image,
                    source=old_image.source,
                    is_primary=old_image.is_primary
                )
                old_image.delete()

            self._migrate_other_names(orm, old_person, new_person)
            self._add_old_identifier(orm, old_person, new_person, 'popoloperson')
            self._migrate_identifiers(orm, old_person, new_person, 'popoloperson')

    def _migrate_other_names(self, orm, old_person, new_person):
        popolo_person_content_type = orm['contenttypes.ContentType'].objects.get(
            app_label="core", model="popoloperson"
        )
        for apn in old_person.alternative_names.all():
            orm.PopoloOtherName.objects.create(
                name=apn.alternative_name,
                note=apn.note,
                name_to_use=apn.name_to_use,
                family_name=apn.family_name,
                given_name=apn.given_name,
                additional_name=apn.additional_name,
                honorific_prefix=apn.honorific_prefix,
                honorific_suffix=apn.honorific_suffix,
                content_type=popolo_person_content_type,
                object_id=new_person.id,
            )

    def _migrate_position_forwards(self, orm):
        GenericRelation(orm.Identifier).contribute_to_class(orm.Position, "core_identifier_set")

        for old_position in orm.Position.objects.all():
            new_membership = orm.PopoloMembership()

            new_membership.person = self._get_new_person(
                orm, old_position.person_id)
            new_membership.organization = self._get_new_organization(
                orm, old_position.organisation_id)

            new_membership.place = old_position.place
            new_membership.title = old_position.title
            new_membership.subtitle = old_position.subtitle
            new_membership.note = old_position.note
            new_membership.category = old_position.category

            new_membership.start_date = repr(old_position.start_date)
            new_membership.end_date = repr(old_position.end_date)

            new_membership.sorting_start_date = old_position.sorting_start_date
            new_membership.sorting_end_date = old_position.sorting_end_date
            new_membership.sorting_start_date_high = old_position.sorting_start_date_high
            new_membership.sorting_end_date_high = old_position.sorting_end_date_high

            new_membership.created_at = old_position.created
            new_membership.updated_at = old_position.updated

            new_membership.save()

            self._add_old_identifier(orm, old_position, new_membership, 'popolomembership')
            self._migrate_identifiers(orm, old_position, new_membership, 'popolomembership')

    def _get_new_person(self, orm, old_pombola_person_id):
        identifier = orm['popolo.Identifier'].objects.get(
            scheme='old_pombola_person_id',
            identifier=str(old_pombola_person_id),
            )

        return orm.PopoloPerson.objects.get(pk=identifier.object_id)

    def _get_new_organization(self, orm, old_pombola_organization_id):
        if old_pombola_organization_id is None:
            # Even the new PopoloOrganization needs an OrganisationKind,
            # since we're mantaining the kind field across the migration,
            # so make sure that there is a placeholder OrganisationKind
            # for the 'unknown' organisation to use.
            placeholder_org_kind, _ = orm.OrganisationKind.objects.get_or_create(
                slug='placeholder',
                defaults={
                    'name': 'Placeholder',
                }
            )
            # Then get or create the special 'unknown' organization to deal
            # with these odd cases.  (We've checked that there are no extant
            # organisations with slug 'unknown' in any Pombola instance.)
            unknown_org, _ = orm.PopoloOrganization.objects.get_or_create(
                slug='unknown',
                kind=placeholder_org_kind,
                defaults={
                    'name': 'Unknown',
                }
            )
            return unknown_org
        identifier = orm['popolo.Identifier'].objects.get(
            scheme='old_pombola_organisation_id',
            identifier=str(old_pombola_organization_id),
            )

        return orm.PopoloOrganization.objects.get(pk=identifier.object_id)

    def _migrate_contact(self, orm, contact, obj, model_name):
        contact_content_type = orm['contenttypes.ContentType'].objects.get(
            app_label="popolo", model="contactdetail"
        )
        object_content_type = orm['contenttypes.ContentType'].objects.get(
            app_label="popolo", model=model_name
        )

        contact_detail = orm['popolo.ContactDetail'].objects.create(
            value=contact.value,
            note=contact.note,
            contact_type=contact.kind.slug,
            label=contact.kind.name,

            object_id=obj.id,
            content_type=object_content_type,
        )
        orm['popolo.Source'].objects.create(
            note=contact.source,
            url=contact.source if self._is_url(contact.source) else '',

            object_id=contact_detail.id,
            content_type=contact_content_type,
        )

    def get_old_pombola_id_scheme(self, popolo_based_model_name):
        return 'old_pombola_{}_id'.format({
            'popoloperson': 'person',
            'popoloorganization': 'organisation',
            'popolomembership': 'position',
        }[popolo_based_model_name])

    def _add_old_identifier(self, orm, old_obj, new_obj, model_name):
        identifier_scheme = self.get_old_pombola_id_scheme(model_name)

        object_content_type = orm['contenttypes.ContentType'].objects.get(
            app_label="core", model=model_name
        )

        # Store the old Pombola identifier
        orm['popolo.Identifier'].objects.create(
            scheme=identifier_scheme,
            identifier='{}'.format(old_obj.id),
            content_type=object_content_type,
            object_id=new_obj.id,
        )

    def _migrate_identifiers(self, orm, old_obj, new_obj, model_name):
        object_content_type = orm['contenttypes.ContentType'].objects.get(
            app_label="core", model=model_name
        )

        for old_identifier in old_obj.core_identifier_set.all():
            orm['popolo.Identifier'].objects.create(
                scheme=old_identifier.scheme,
                identifier=old_identifier.identifier,
                content_type=object_content_type,
                object_id=new_obj.id,
            )

    def backwards(self, orm):
        # If you really want to run this backwards migration, it should be tested
        # in a safe test environment first, so we're raising an Exception here to
        # make sure that no one runs it on a production dataset assuming that it
        # will Just Work.
        raise Exception, "Warning: this backwards migration hasn't been tested"
        orm.PopoloOrganization.objects.all().delete()
        orm.PopoloPerson.objects.all().delete()
        orm.PopoloMembership.objects.all().delete()
        orm['popolo.ContactDetail'].objects.all().delete()

    models = {
        u'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        u'core.alternativepersonname': {
            'Meta': {'unique_together': "(('person', 'alternative_name'),)", 'object_name': 'AlternativePersonName'},
            'additional_name': ('django.db.models.fields.CharField', [], {'max_length': '300', 'blank': 'True'}),
            'alternative_name': ('django.db.models.fields.CharField', [], {'max_length': '300'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'end_date': ('django_date_extensions.fields.ApproximateDateField', [], {'max_length': '10', 'blank': 'True'}),
            'family_name': ('django.db.models.fields.CharField', [], {'max_length': '300', 'blank': 'True'}),
            'given_name': ('django.db.models.fields.CharField', [], {'max_length': '300', 'blank': 'True'}),
            'honorific_prefix': ('django.db.models.fields.CharField', [], {'max_length': '300', 'blank': 'True'}),
            'honorific_suffix': ('django.db.models.fields.CharField', [], {'max_length': '300', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name_to_use': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'note': ('django.db.models.fields.CharField', [], {'max_length': '300', 'blank': 'True'}),
            'person': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'alternative_names'", 'to': u"orm['core.Person']"}),
            'start_date': ('django_date_extensions.fields.ApproximateDateField', [], {'max_length': '10', 'blank': 'True'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        },
        u'core.contact': {
            'Meta': {'ordering': "['content_type', 'object_id', 'kind']", 'object_name': 'Contact'},
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']"}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'kind': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['core.ContactKind']"}),
            'note': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'object_id': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'source': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '500', 'blank': 'True'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'value': ('django.db.models.fields.TextField', [], {})
        },
        u'core.contactkind': {
            'Meta': {'ordering': "['slug']", 'object_name': 'ContactKind'},
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '200'}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '200'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        },
        u'core.identifier': {
            'Meta': {'unique_together': "(('scheme', 'identifier'),)", 'object_name': 'Identifier'},
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'core_identifier_set'", 'to': u"orm['contenttypes.ContentType']"}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'identifier': ('django.db.models.fields.CharField', [], {'max_length': '500'}),
            'object_id': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'scheme': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        },
        u'core.informationsource': {
            'Meta': {'ordering': "['content_type', 'object_id', 'source']", 'object_name': 'InformationSource'},
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']"}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'entered': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'note': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'object_id': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'source': ('django.db.models.fields.CharField', [], {'max_length': '500'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        },
        u'core.organisation': {
            'Meta': {'ordering': "['slug']", 'object_name': 'Organisation'},
            u'_summary_rendered': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'ended': ('django_date_extensions.fields.ApproximateDateField', [], {'max_length': '10', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'kind': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['core.OrganisationKind']"}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '200'}),
            'started': ('django_date_extensions.fields.ApproximateDateField', [], {'max_length': '10', 'blank': 'True'}),
            'summary': ('markitup.fields.MarkupField', [], {'default': "''", u'no_rendered_field': 'True', 'blank': 'True'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
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
        u'core.organisationrelationship': {
            'Meta': {'object_name': 'OrganisationRelationship'},
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'kind': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['core.OrganisationRelationshipKind']"}),
            'organisation_a': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'org_rels_as_a'", 'to': u"orm['core.Organisation']"}),
            'organisation_b': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'org_rels_as_b'", 'to': u"orm['core.Organisation']"}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        },
        u'core.organisationrelationshipkind': {
            'Meta': {'object_name': 'OrganisationRelationshipKind'},
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '200'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        },
        u'core.parliamentarysession': {
            'Meta': {'ordering': "['start_date']", 'object_name': 'ParliamentarySession'},
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'end_date': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'house': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['core.Organisation']"}),
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
        u'core.place': {
            'Meta': {'ordering': "['slug']", 'object_name': 'Place'},
            u'_summary_rendered': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'kind': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['core.PlaceKind']"}),
            'location': ('django.contrib.gis.db.models.fields.PointField', [], {'null': 'True', 'blank': 'True'}),
            'mapit_area': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['mapit.Area']", 'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'organisation': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['core.Organisation']", 'null': 'True', 'blank': 'True'}),
            'parent_place': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'child_places'", 'null': 'True', 'to': u"orm['core.Place']"}),
            'parliamentary_session': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['core.ParliamentarySession']", 'null': 'True', 'blank': 'True'}),
            'shape_url': ('django.db.models.fields.URLField', [], {'max_length': '200', 'blank': 'True'}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '200'}),
            'summary': ('markitup.fields.MarkupField', [], {'default': "''", u'no_rendered_field': 'True', 'blank': 'True'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        },
        u'core.placekind': {
            'Meta': {'ordering': "['slug']", 'object_name': 'PlaceKind'},
            u'_summary_rendered': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '200'}),
            'plural_name': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '200'}),
            'summary': ('markitup.fields.MarkupField', [], {'default': "''", u'no_rendered_field': 'True', 'blank': 'True'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        },
        u'core.popolomembership': {
            'Meta': {'object_name': 'PopoloMembership', '_ormbases': [u'popolo.Membership']},
            'category': ('django.db.models.fields.CharField', [], {'default': "'other'", 'max_length': '20'}),
            u'membership_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['popolo.Membership']", 'unique': 'True', 'primary_key': 'True'}),
            'note': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '300', 'blank': 'True'}),
            'place': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['core.Place']", 'null': 'True', 'blank': 'True'}),
            'sorting_end_date': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '10'}),
            'sorting_end_date_high': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '10'}),
            'sorting_start_date': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '10'}),
            'sorting_start_date_high': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '10'}),
            'subtitle': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '200', 'blank': 'True'}),
            'title': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['core.PositionTitle']", 'null': 'True', 'blank': 'True'})
        },
        u'core.popoloorganization': {
            'Meta': {'object_name': 'PopoloOrganization', '_ormbases': [u'popolo.Organization']},
            u'_summary_rendered': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'kind': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['core.OrganisationKind']"}),
            u'organization_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['popolo.Organization']", 'unique': 'True', 'primary_key': 'True'}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '200'}),
            'summary': ('markitup.fields.MarkupField', [], {'default': "''", u'no_rendered_field': 'True', 'blank': 'True'})
        },
        u'core.popoloothername': {
            'Meta': {'object_name': 'PopoloOtherName', '_ormbases': [u'popolo.OtherName']},
            'additional_name': ('django.db.models.fields.CharField', [], {'max_length': '300', 'blank': 'True'}),
            'family_name': ('django.db.models.fields.CharField', [], {'max_length': '300', 'blank': 'True'}),
            'given_name': ('django.db.models.fields.CharField', [], {'max_length': '300', 'blank': 'True'}),
            'honorific_prefix': ('django.db.models.fields.CharField', [], {'max_length': '300', 'blank': 'True'}),
            'honorific_suffix': ('django.db.models.fields.CharField', [], {'max_length': '300', 'blank': 'True'}),
            'name_to_use': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            u'othername_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['popolo.OtherName']", 'unique': 'True', 'primary_key': 'True'})
        },
        u'core.popoloperson': {
            'Meta': {'object_name': 'PopoloPerson', '_ormbases': [u'popolo.Person']},
            'can_be_featured': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'hidden': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            u'person_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['popolo.Person']", 'unique': 'True', 'primary_key': 'True'}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '200'})
        },
        u'core.position': {
            'Meta': {'ordering': "['-sorting_end_date', '-sorting_start_date']", 'object_name': 'Position'},
            'category': ('django.db.models.fields.CharField', [], {'default': "'other'", 'max_length': '20'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'end_date': ('django_date_extensions.fields.ApproximateDateField', [], {'default': "'future'", 'max_length': '10', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'note': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '300', 'blank': 'True'}),
            'organisation': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['core.Organisation']", 'null': 'True', 'blank': 'True'}),
            'person': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['core.Person']"}),
            'place': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['core.Place']", 'null': 'True', 'blank': 'True'}),
            'sorting_end_date': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '10'}),
            'sorting_end_date_high': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '10'}),
            'sorting_start_date': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '10'}),
            'sorting_start_date_high': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '10'}),
            'start_date': ('django_date_extensions.fields.ApproximateDateField', [], {'max_length': '10', 'blank': 'True'}),
            'subtitle': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '200', 'blank': 'True'}),
            'title': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['core.PositionTitle']", 'null': 'True', 'blank': 'True'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        },
        u'core.positiontitle': {
            'Meta': {'ordering': "['slug']", 'object_name': 'PositionTitle'},
            u'_summary_rendered': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '200'}),
            'requires_place': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '200'}),
            'summary': ('markitup.fields.MarkupField', [], {'default': "''", u'no_rendered_field': 'True', 'blank': 'True'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        },
        u'images.image': {
            'Meta': {'object_name': 'Image'},
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'image': (u'sorl.thumbnail.fields.ImageField', [], {'max_length': '100'}),
            'is_primary': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'object_id': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'source': ('django.db.models.fields.CharField', [], {'max_length': '400'})
        },
        u'mapit.area': {
            'Meta': {'ordering': "('name', 'type')", 'object_name': 'Area'},
            'country': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'areas'", 'null': 'True', 'to': u"orm['mapit.Country']"}),
            'generation_high': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'final_areas'", 'null': 'True', 'to': u"orm['mapit.Generation']"}),
            'generation_low': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'new_areas'", 'null': 'True', 'to': u"orm['mapit.Generation']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '2000', 'blank': 'True'}),
            'parent_area': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'children'", 'null': 'True', 'to': u"orm['mapit.Area']"}),
            'type': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'areas'", 'to': u"orm['mapit.Type']"})
        },
        u'mapit.country': {
            'Meta': {'object_name': 'Country'},
            'code': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '3'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '100'})
        },
        u'mapit.generation': {
            'Meta': {'object_name': 'Generation'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        u'mapit.type': {
            'Meta': {'object_name': 'Type'},
            'code': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '500'}),
            'description': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        u'popolo.contactdetail': {
            'Meta': {'object_name': 'ContactDetail'},
            'contact_type': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']"}),
            'created_at': ('model_utils.fields.AutoCreatedField', [], {'default': 'datetime.datetime.now'}),
            'end_date': ('django.db.models.fields.CharField', [], {'max_length': '10', 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'label': ('django.db.models.fields.CharField', [], {'max_length': '4000', 'blank': 'True'}),
            'note': ('django.db.models.fields.CharField', [], {'max_length': '4000', 'blank': 'True'}),
            'object_id': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'start_date': ('django.db.models.fields.CharField', [], {'max_length': '10', 'null': 'True', 'blank': 'True'}),
            'updated_at': ('model_utils.fields.AutoLastModifiedField', [], {'default': 'datetime.datetime.now'}),
            'value': ('django.db.models.fields.CharField', [], {'max_length': '4000'})
        },
        u'popolo.identifier': {
            'Meta': {'object_name': 'Identifier'},
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'identifier': ('django.db.models.fields.CharField', [], {'max_length': '4000'}),
            'object_id': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'scheme': ('django.db.models.fields.CharField', [], {'max_length': '4000', 'blank': 'True'})
        },
        u'popolo.link': {
            'Meta': {'object_name': 'Link'},
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'note': ('django.db.models.fields.CharField', [], {'max_length': '4000', 'blank': 'True'}),
            'object_id': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'url': ('django.db.models.fields.URLField', [], {'max_length': '200'})
        },
        u'popolo.membership': {
            'Meta': {'object_name': 'Membership'},
            'created_at': ('model_utils.fields.AutoCreatedField', [], {'default': 'datetime.datetime.now'}),
            'end_date': ('django.db.models.fields.CharField', [], {'max_length': '10', 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'label': ('django.db.models.fields.CharField', [], {'max_length': '4000', 'blank': 'True'}),
            'on_behalf_of': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'memberships_on_behalf_of'", 'null': 'True', 'to': u"orm['popolo.Organization']"}),
            'organization': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'memberships'", 'to': u"orm['popolo.Organization']"}),
            'person': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'memberships'", 'to': u"orm['popolo.Person']"}),
            'post': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'memberships'", 'null': 'True', 'to': u"orm['popolo.Post']"}),
            'role': ('django.db.models.fields.CharField', [], {'max_length': '4000', 'blank': 'True'}),
            'start_date': ('django.db.models.fields.CharField', [], {'max_length': '10', 'null': 'True', 'blank': 'True'}),
            'updated_at': ('model_utils.fields.AutoLastModifiedField', [], {'default': 'datetime.datetime.now'})
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
        u'popolo.othername': {
            'Meta': {'object_name': 'OtherName'},
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']"}),
            'end_date': ('django.db.models.fields.CharField', [], {'max_length': '10', 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '4000'}),
            'note': ('django.db.models.fields.CharField', [], {'max_length': '4000', 'blank': 'True'}),
            'object_id': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'start_date': ('django.db.models.fields.CharField', [], {'max_length': '10', 'null': 'True', 'blank': 'True'})
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
        },
        u'popolo.post': {
            'Meta': {'object_name': 'Post'},
            'created_at': ('model_utils.fields.AutoCreatedField', [], {'default': 'datetime.datetime.now'}),
            'end_date': ('django.db.models.fields.CharField', [], {'max_length': '10', 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'label': ('django.db.models.fields.CharField', [], {'max_length': '4000'}),
            'organization': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'posts'", 'to': u"orm['popolo.Organization']"}),
            'role': ('django.db.models.fields.CharField', [], {'max_length': '4000', 'blank': 'True'}),
            'start_date': ('django.db.models.fields.CharField', [], {'max_length': '10', 'null': 'True', 'blank': 'True'}),
            'updated_at': ('model_utils.fields.AutoLastModifiedField', [], {'default': 'datetime.datetime.now'})
        },
        u'popolo.source': {
            'Meta': {'object_name': 'Source'},
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'note': ('django.db.models.fields.CharField', [], {'max_length': '4000', 'blank': 'True'}),
            'object_id': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'url': ('django.db.models.fields.URLField', [], {'max_length': '200'})
        }
    }

    complete_apps = ['popolo', 'images', 'core']
    symmetrical = True

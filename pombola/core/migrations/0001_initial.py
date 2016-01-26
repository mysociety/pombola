# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django_date_extensions.fields
import pombola.images.models
import pombola.core.models
import markitup.fields
import django.contrib.gis.db.models.fields


class Migration(migrations.Migration):

    dependencies = [
        ('mapit', '0002_auto_20141218_1615'),
        ('contenttypes', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='AlternativePersonName',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('updated', models.DateTimeField(auto_now=True)),
                ('alternative_name', models.CharField(max_length=300)),
                ('name_to_use', models.BooleanField(default=False)),
                ('start_date', django_date_extensions.fields.ApproximateDateField(help_text=b"Format: '2011-12-31', '31 Jan 2011', 'Jan 2011' or '2011' or 'future'", max_length=10, blank=True)),
                ('end_date', django_date_extensions.fields.ApproximateDateField(help_text=b"Format: '2011-12-31', '31 Jan 2011', 'Jan 2011' or '2011' or 'future'", max_length=10, blank=True)),
                ('note', models.CharField(max_length=300, blank=True)),
                ('family_name', models.CharField(max_length=300, blank=True)),
                ('given_name', models.CharField(max_length=300, blank=True)),
                ('additional_name', models.CharField(max_length=300, blank=True)),
                ('honorific_prefix', models.CharField(max_length=300, blank=True)),
                ('honorific_suffix', models.CharField(max_length=300, blank=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Contact',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('updated', models.DateTimeField(auto_now=True)),
                ('value', models.TextField()),
                ('note', models.TextField(help_text=b'publicly visible, use to clarify contact detail', blank=True)),
                ('source', models.CharField(default=b'', help_text=b'where did this contact detail come from', max_length=500, blank=True)),
                ('object_id', models.PositiveIntegerField()),
                ('content_type', models.ForeignKey(to='contenttypes.ContentType')),
            ],
            options={
                'ordering': ['content_type', 'object_id', 'kind'],
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ContactKind',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('updated', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(unique=True, max_length=200)),
                ('slug', models.SlugField(help_text=b'created from name', unique=True, max_length=200)),
            ],
            options={
                'ordering': ['slug'],
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Identifier',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('updated', models.DateTimeField(auto_now=True)),
                ('scheme', models.CharField(max_length=200)),
                ('identifier', models.CharField(max_length=500)),
                ('object_id', models.PositiveIntegerField()),
                ('content_type', models.ForeignKey(related_name='pombola_identifier_set', to='contenttypes.ContentType')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='InformationSource',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('updated', models.DateTimeField(auto_now=True)),
                ('source', models.CharField(max_length=500)),
                ('note', models.TextField(blank=True)),
                ('entered', models.BooleanField(default=False, help_text=b'has the information in this source been entered into this system?')),
                ('object_id', models.PositiveIntegerField()),
                ('content_type', models.ForeignKey(to='contenttypes.ContentType')),
            ],
            options={
                'ordering': ['content_type', 'object_id', 'source'],
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Organisation',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('updated', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(max_length=200)),
                ('slug', models.SlugField(help_text=b'created from name', unique=True, max_length=200, validators=[pombola.core.models.validate_organisation_slug])),
                ('summary', markitup.fields.MarkupField(default=b'', no_rendered_field=True, blank=True)),
                ('started', django_date_extensions.fields.ApproximateDateField(help_text=b"Format: '2011-12-31', '31 Jan 2011', 'Jan 2011' or '2011' or 'future'", max_length=10, blank=True)),
                ('ended', django_date_extensions.fields.ApproximateDateField(help_text=b"Format: '2011-12-31', '31 Jan 2011', 'Jan 2011' or '2011' or 'future'", max_length=10, blank=True)),
                ('_summary_rendered', models.TextField(editable=False, blank=True)),
            ],
            options={
                'ordering': ['slug'],
            },
            bases=(models.Model, pombola.images.models.HasImageMixin, pombola.core.models.IdentifierMixin),
        ),
        migrations.CreateModel(
            name='OrganisationKind',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('updated', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(unique=True, max_length=200)),
                ('slug', models.SlugField(help_text=b'created from name', unique=True, max_length=200)),
                ('summary', markitup.fields.MarkupField(default=b'', no_rendered_field=True, blank=True)),
                ('_summary_rendered', models.TextField(editable=False, blank=True)),
            ],
            options={
                'ordering': ['slug'],
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='OrganisationRelationship',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('updated', models.DateTimeField(auto_now=True)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='OrganisationRelationshipKind',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('updated', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(unique=True, max_length=200)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ParliamentarySession',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('updated', models.DateTimeField(auto_now=True)),
                ('start_date', models.DateField(null=True, blank=True)),
                ('end_date', models.DateField(null=True, blank=True)),
                ('mapit_generation', models.PositiveIntegerField(help_text=b'The MapIt generation with boundaries for this session', null=True, blank=True)),
                ('name', models.CharField(unique=True, max_length=200)),
                ('slug', models.SlugField(help_text=b'specify manually', unique=True, max_length=200)),
                ('house', models.ForeignKey(to='core.Organisation')),
            ],
            options={
                'ordering': ['start_date'],
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Person',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('updated', models.DateTimeField(auto_now=True)),
                ('title', models.CharField(max_length=100, blank=True)),
                ('legal_name', models.CharField(max_length=300)),
                ('slug', models.SlugField(help_text=b'auto-created from first name and last name', unique=True, max_length=200, validators=[pombola.core.models.validate_person_slug])),
                ('gender', models.CharField(help_text=b"this is typically, but not restricted to, 'male' or 'female'", max_length=20, blank=True)),
                ('date_of_birth', django_date_extensions.fields.ApproximateDateField(help_text=b"Format: '2011-12-31', '31 Jan 2011', 'Jan 2011' or '2011' or 'future'", max_length=10, blank=True)),
                ('date_of_death', django_date_extensions.fields.ApproximateDateField(help_text=b"Format: '2011-12-31', '31 Jan 2011', 'Jan 2011' or '2011' or 'future'", max_length=10, blank=True)),
                ('summary', markitup.fields.MarkupField(default=b'', no_rendered_field=True, blank=True)),
                ('email', models.EmailField(max_length=75, blank=True)),
                ('hidden', models.BooleanField(default=False, help_text=b"hide this person's pages from normal users")),
                ('can_be_featured', models.BooleanField(default=False, help_text=b'can this person be featured on the home page (e.g., is their data appropriate and extant)?')),
                ('biography', markitup.fields.MarkupField(default=b'', no_rendered_field=True, blank=True)),
                ('national_identity', models.CharField(max_length=100, blank=True)),
                ('family_name', models.CharField(max_length=300, blank=True)),
                ('given_name', models.CharField(max_length=300, blank=True)),
                ('additional_name', models.CharField(max_length=300, blank=True)),
                ('honorific_prefix', models.CharField(max_length=300, blank=True)),
                ('honorific_suffix', models.CharField(max_length=300, blank=True)),
                ('sort_name', models.CharField(max_length=300, blank=True)),
                ('_biography_rendered', models.TextField(editable=False, blank=True)),
                ('_summary_rendered', models.TextField(editable=False, blank=True)),
            ],
            options={
                'ordering': ['sort_name'],
            },
            bases=(pombola.images.models.HasImageMixin, models.Model, pombola.core.models.IdentifierMixin),
        ),
        migrations.CreateModel(
            name='Place',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('updated', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(max_length=200)),
                ('slug', models.SlugField(help_text=b'created from name', unique=True, max_length=200, validators=[pombola.core.models.validate_place_slug])),
                ('summary', markitup.fields.MarkupField(default=b'', no_rendered_field=True, blank=True)),
                ('shape_url', models.URLField(blank=True)),
                ('location', django.contrib.gis.db.models.fields.PointField(srid=4326, null=True, blank=True)),
                ('_summary_rendered', models.TextField(editable=False, blank=True)),
            ],
            options={
                'ordering': ['slug'],
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='PlaceKind',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('updated', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(unique=True, max_length=200)),
                ('plural_name', models.CharField(max_length=200, blank=True)),
                ('slug', models.SlugField(help_text=b'created from name', unique=True, max_length=200)),
                ('summary', markitup.fields.MarkupField(default=b'', no_rendered_field=True, blank=True)),
                ('_summary_rendered', models.TextField(editable=False, blank=True)),
            ],
            options={
                'ordering': ['slug'],
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Position',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('updated', models.DateTimeField(auto_now=True)),
                ('subtitle', models.CharField(default=b'', max_length=200, blank=True)),
                ('category', models.CharField(default=b'other', help_text=b'What sort of position was this?', max_length=20, choices=[(b'political', b'Political'), (b'education', b'Education (as a learner)'), (b'other', b'Anything else')])),
                ('note', models.CharField(default=b'', max_length=300, blank=True)),
                ('start_date', django_date_extensions.fields.ApproximateDateField(help_text=b"Format: '2011-12-31', '31 Jan 2011', 'Jan 2011' or '2011' or 'future'", max_length=10, blank=True)),
                ('end_date', django_date_extensions.fields.ApproximateDateField(default=b'future', help_text=b"Format: '2011-12-31', '31 Jan 2011', 'Jan 2011' or '2011' or 'future'", max_length=10, blank=True)),
                ('sorting_start_date', models.CharField(default=b'', max_length=10)),
                ('sorting_end_date', models.CharField(default=b'', max_length=10)),
                ('sorting_start_date_high', models.CharField(default=b'', max_length=10)),
                ('sorting_end_date_high', models.CharField(default=b'', max_length=10)),
                ('organisation', models.ForeignKey(blank=True, to='core.Organisation', null=True)),
                ('person', models.ForeignKey(to='core.Person')),
                ('place', models.ForeignKey(blank=True, to='core.Place', help_text=b'use if needed to identify the position - eg add constituency for a politician', null=True)),
            ],
            options={
                'ordering': ['-sorting_end_date', '-sorting_start_date'],
            },
            bases=(models.Model, pombola.core.models.IdentifierMixin),
        ),
        migrations.CreateModel(
            name='PositionTitle',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('updated', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(unique=True, max_length=200)),
                ('slug', models.SlugField(help_text=b'created from name', unique=True, max_length=200)),
                ('summary', markitup.fields.MarkupField(default=b'', no_rendered_field=True, blank=True)),
                ('requires_place', models.BooleanField(default=False, help_text=b'Does this job title require a place to complete the position?')),
                ('_summary_rendered', models.TextField(editable=False, blank=True)),
            ],
            options={
                'ordering': ['slug'],
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='position',
            name='title',
            field=models.ForeignKey(blank=True, to='core.PositionTitle', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='place',
            name='kind',
            field=models.ForeignKey(to='core.PlaceKind'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='place',
            name='mapit_area',
            field=models.ForeignKey(blank=True, to='mapit.Area', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='place',
            name='organisation',
            field=models.ForeignKey(blank=True, to='core.Organisation', help_text=b'use if the place uniquely belongs to an organisation - eg a field office', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='place',
            name='parent_place',
            field=models.ForeignKey(related_name='child_places', blank=True, to='core.Place', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='place',
            name='parliamentary_session',
            field=models.ForeignKey(blank=True, to='core.ParliamentarySession', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='organisationrelationship',
            name='kind',
            field=models.ForeignKey(to='core.OrganisationRelationshipKind'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='organisationrelationship',
            name='organisation_a',
            field=models.ForeignKey(related_name='org_rels_as_a', to='core.Organisation'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='organisationrelationship',
            name='organisation_b',
            field=models.ForeignKey(related_name='org_rels_as_b', to='core.Organisation'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='organisation',
            name='kind',
            field=models.ForeignKey(to='core.OrganisationKind'),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name='identifier',
            unique_together=set([('scheme', 'identifier')]),
        ),
        migrations.AddField(
            model_name='contact',
            name='kind',
            field=models.ForeignKey(to='core.ContactKind'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='alternativepersonname',
            name='person',
            field=models.ForeignKey(related_name='alternative_names', to='core.Person'),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name='alternativepersonname',
            unique_together=set([('person', 'alternative_name')]),
        ),
    ]

# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('speeches', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Answer',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('document_name', models.TextField()),
                ('oral_number', models.IntegerField(null=True, db_index=True)),
                ('written_number', models.IntegerField(null=True, db_index=True)),
                ('president_number', models.IntegerField(null=True, db_index=True)),
                ('dp_number', models.IntegerField(null=True, db_index=True)),
                ('date', models.DateField()),
                ('year', models.IntegerField(db_index=True)),
                ('house', models.CharField(db_index=True, max_length=1, choices=[(b'N', b'National Assembly'), (b'C', b'National Council of Provinces')])),
                ('text', models.TextField()),
                ('processed_code', models.IntegerField(default=0, db_index=True, choices=[(0, b'pending'), (1, b'OK'), (2, b'HTTP error')])),
                ('name', models.TextField()),
                ('language', models.TextField()),
                ('url', models.TextField(db_index=True)),
                ('date_published', models.DateField()),
                ('type', models.TextField()),
                ('last_sayit_import', models.DateTimeField(null=True, blank=True)),
                ('sayit_section', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, blank=True, to='speeches.Section', help_text=b'Associated Sayit section object, if imported', null=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='PMGCommitteeAppearance',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('party', models.TextField()),
                ('person', models.TextField()),
                ('text', models.TextField()),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='PMGCommitteeReport',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('premium', models.BooleanField(default=None)),
                ('processed', models.BooleanField(default=None)),
                ('meeting_url', models.TextField()),
                ('meeting_name', models.TextField(null=True, blank=True)),
                ('committee_url', models.URLField(null=True, blank=True)),
                ('committee_name', models.TextField(default=b'')),
                ('meeting_date', models.DateField(null=True, blank=True)),
                ('api_committee_id', models.IntegerField(null=True, blank=True)),
                ('api_meeting_id', models.IntegerField(null=True, blank=True)),
                ('last_sayit_import', models.DateTimeField(null=True, blank=True)),
                ('sayit_section', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, blank=True, to='speeches.Section', help_text=b'Associated Sayit section object, if imported', null=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Question',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('written_number', models.IntegerField(null=True, db_index=True)),
                ('oral_number', models.IntegerField(null=True, db_index=True)),
                ('president_number', models.IntegerField(null=True, db_index=True)),
                ('dp_number', models.IntegerField(null=True, db_index=True)),
                ('identifier', models.CharField(max_length=10, db_index=True)),
                ('id_number', models.IntegerField(db_index=True)),
                ('house', models.CharField(db_index=True, max_length=1, choices=[(b'N', b'National Assembly'), (b'C', b'National Council of Provinces')])),
                ('answer_type', models.CharField(max_length=1, choices=[(b'O', b'Oral Answer'), (b'W', b'Written Answer')])),
                ('date', models.DateField()),
                ('year', models.IntegerField(db_index=True)),
                ('date_transferred', models.DateField(null=True)),
                ('question', models.TextField()),
                ('questionto', models.TextField()),
                ('translated', models.BooleanField(default=None)),
                ('intro', models.TextField()),
                ('askedby', models.TextField()),
                ('last_sayit_import', models.DateTimeField(null=True, blank=True)),
                ('answer', models.ForeignKey(related_name='question', to='za_hansard.Answer', null=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='QuestionPaper',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('document_name', models.TextField(max_length=32)),
                ('date_published', models.DateField()),
                ('house', models.CharField(max_length=64)),
                ('language', models.CharField(max_length=16)),
                ('document_number', models.IntegerField()),
                ('source_url', models.URLField(max_length=1000)),
                ('year', models.IntegerField()),
                ('issue_number', models.IntegerField()),
                ('parliament_number', models.IntegerField()),
                ('session_number', models.IntegerField()),
                ('text', models.TextField()),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Source',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('title', models.CharField(max_length=200)),
                ('document_name', models.CharField(max_length=200)),
                ('document_number', models.IntegerField(unique=True)),
                ('date', models.DateField()),
                ('url', models.URLField(max_length=1000)),
                ('is404', models.BooleanField(default=False)),
                ('house', models.CharField(max_length=200)),
                ('language', models.CharField(max_length=200)),
                ('last_processing_attempt', models.DateTimeField(null=True, blank=True)),
                ('last_processing_success', models.DateTimeField(null=True, blank=True)),
                ('last_sayit_import', models.DateTimeField(null=True, blank=True)),
                ('sayit_section', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, blank=True, to='speeches.Section', help_text=b'Associated Sayit section object, if imported', null=True)),
            ],
            options={
                'ordering': ['-date', 'document_name'],
            },
            bases=(models.Model,),
        ),
        migrations.AlterUniqueTogether(
            name='questionpaper',
            unique_together=set([('year', 'issue_number', 'house', 'parliament_number')]),
        ),
        migrations.AddField(
            model_name='question',
            name='paper',
            field=models.ForeignKey(on_delete=django.db.models.deletion.SET_NULL, to='za_hansard.QuestionPaper', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='question',
            name='sayit_section',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, blank=True, to='speeches.Section', help_text=b'Associated Sayit section object, if imported', null=True),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name='question',
            unique_together=set([('written_number', 'house', 'year'), ('dp_number', 'house', 'year'), ('oral_number', 'house', 'year'), ('president_number', 'house', 'year'), ('id_number', 'house', 'year')]),
        ),
        migrations.AddField(
            model_name='pmgcommitteeappearance',
            name='report',
            field=models.ForeignKey(related_name='appearances', to='za_hansard.PMGCommitteeReport', null=True),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name='answer',
            unique_together=set([('written_number', 'house', 'year'), ('dp_number', 'house', 'year'), ('oral_number', 'house', 'year'), ('president_number', 'house', 'year')]),
        ),
    ]

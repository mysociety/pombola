# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import datetime


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0002_add_related_name'),
    ]

    operations = [
        migrations.CreateModel(
            name='Alias',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(default=datetime.datetime.now, auto_now_add=True)),
                ('updated', models.DateTimeField(default=datetime.datetime.now, auto_now=True)),
                ('alias', models.CharField(unique=True, max_length=200)),
                ('ignored', models.BooleanField(default=False)),
                ('person', models.ForeignKey(blank=True, to='core.Person', null=True)),
            ],
            options={
                'ordering': ['alias'],
                'verbose_name_plural': 'aliases',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Entry',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('type', models.CharField(max_length=20, choices=[(b'heading', b'Heading'), (b'scene', b'Description of event'), (b'speech', b'Speech'), (b'other', b'Other')])),
                ('page_number', models.IntegerField(blank=True)),
                ('text_counter', models.IntegerField()),
                ('speaker_name', models.CharField(max_length=200, blank=True)),
                ('speaker_title', models.CharField(max_length=200, blank=True)),
                ('content', models.TextField()),
            ],
            options={
                'ordering': ['sitting', 'text_counter'],
                'verbose_name_plural': 'entries',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Sitting',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('start_date', models.DateField()),
                ('start_time', models.TimeField(null=True, blank=True)),
                ('end_date', models.DateField(null=True, blank=True)),
                ('end_time', models.TimeField(null=True, blank=True)),
            ],
            options={
                'ordering': ['-start_date'],
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Source',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=200)),
                ('date', models.DateField()),
                ('url', models.URLField(max_length=1000)),
                ('list_page', models.CharField(help_text=b'A code describing the list page from which the source was found', max_length=50, null=True, blank=True)),
                ('last_processing_attempt', models.DateTimeField(null=True, blank=True)),
                ('last_processing_success', models.DateTimeField(null=True, blank=True)),
            ],
            options={
                'ordering': ['-date', 'name'],
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Venue',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=200)),
                ('slug', models.SlugField(unique=True)),
            ],
            options={
                'ordering': ['slug'],
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='sitting',
            name='source',
            field=models.ForeignKey(to='hansard.Source'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='sitting',
            name='venue',
            field=models.ForeignKey(to='hansard.Venue'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='entry',
            name='sitting',
            field=models.ForeignKey(to='hansard.Sitting'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='entry',
            name='speaker',
            field=models.ForeignKey(related_name='hansard_entries', blank=True, to='core.Person', null=True),
            preserve_default=True,
        ),
    ]

# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import datetime
import markitup.fields


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Category',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(default=datetime.datetime.now, auto_now_add=True)),
                ('updated', models.DateTimeField(default=datetime.datetime.now, auto_now=True)),
                ('name', models.CharField(unique=True, max_length=200)),
                ('slug', models.SlugField(unique=True)),
                ('synopsis', models.CharField(max_length=200)),
                ('description', markitup.fields.MarkupField(no_rendered_field=True)),
                ('_description_rendered', models.TextField(editable=False, blank=True)),
            ],
            options={
                'ordering': ('name',),
                'verbose_name_plural': 'categories',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Entry',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(default=datetime.datetime.now, auto_now_add=True)),
                ('updated', models.DateTimeField(default=datetime.datetime.now, auto_now=True)),
                ('object_id', models.PositiveIntegerField()),
                ('date', models.DateField()),
                ('disabled', models.BooleanField(default=False)),
                ('disabled_comment', models.CharField(default=b'', help_text=b"A comment to explain why the scorecard is disabled - eg 'No data is available'", max_length=300, blank=True)),
                ('remark', models.CharField(max_length=150)),
                ('extended_remark', markitup.fields.MarkupField(help_text=b'Extra details about the entry, not shown in summary view.', max_length=1000, no_rendered_field=True, blank=True)),
                ('score', models.IntegerField(choices=[(1, b'Good (+1)'), (0, b'Neutral (0)'), (-1, b'Bad (-1)')])),
                ('equivalent_remark', markitup.fields.MarkupField(help_text=b'Please **bold** the relevant part - eg "Enough money is going missing to pay for **123 teachers**"', max_length=400, no_rendered_field=True, blank=True)),
                ('source_url', models.URLField(blank=True)),
                ('source_name', models.CharField(max_length=200, blank=True)),
                ('_equivalent_remark_rendered', models.TextField(editable=False, blank=True)),
                ('_extended_remark_rendered', models.TextField(editable=False, blank=True)),
                ('category', models.ForeignKey(to='scorecards.Category')),
                ('content_type', models.ForeignKey(to='contenttypes.ContentType')),
            ],
            options={
                'ordering': ('-date', 'category'),
                'verbose_name_plural': 'entries',
            },
            bases=(models.Model,),
        ),
        migrations.AlterUniqueTogether(
            name='entry',
            unique_together=set([('content_type', 'object_id', 'category', 'date')]),
        ),
    ]

# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import datetime
import markitup.fields


class Migration(migrations.Migration):

    dependencies = [
        ('file_archive', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Category',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(default=datetime.datetime.now, auto_now_add=True)),
                ('updated', models.DateTimeField(default=datetime.datetime.now, auto_now=True)),
                ('name', models.CharField(unique=True, max_length=300)),
                ('slug', models.SlugField(unique=True)),
                ('summary', markitup.fields.MarkupField(no_rendered_field=True, blank=True)),
                ('_summary_rendered', models.TextField(editable=False, blank=True)),
            ],
            options={
                'verbose_name_plural': 'categories',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='InfoPage',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(default=datetime.datetime.now, auto_now_add=True)),
                ('updated', models.DateTimeField(default=datetime.datetime.now, auto_now=True)),
                ('title', models.CharField(unique=True, max_length=300)),
                ('slug', models.SlugField(unique=True)),
                ('markdown_content', markitup.fields.MarkupField(default=b'', help_text=b'When linking to other pages use their slugs as the address (note that these links do not work in the preview, but will on the real site)', no_rendered_field=True, blank=True)),
                ('raw_content', models.TextField(default=b'', help_text=b"You can enter raw HTML into this box, and it will be used if 'Enter content as raw HTML' is selected", verbose_name=b'Raw HTML', blank=True)),
                ('use_raw', models.BooleanField(default=False, verbose_name=b'Enter content as raw HTML')),
                ('kind', models.CharField(default=b'page', max_length=10, choices=[(b'blog', b'Blog'), (b'page', b'Page')])),
                ('publication_date', models.DateTimeField(default=datetime.datetime.now)),
                ('_markdown_content_rendered', models.TextField(editable=False, blank=True)),
                ('categories', models.ManyToManyField(related_name='entries', to='info.Category', blank=True)),
                ('featured_image_file', models.ForeignKey(blank=True, to='file_archive.File', null=True)),
            ],
            options={
                'ordering': ['title'],
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Tag',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(default=datetime.datetime.now, auto_now_add=True)),
                ('updated', models.DateTimeField(default=datetime.datetime.now, auto_now=True)),
                ('name', models.CharField(unique=True, max_length=300)),
                ('slug', models.SlugField(unique=True)),
            ],
            options={
                'ordering': ('name',),
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ViewCount',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('date', models.DateField()),
                ('count', models.IntegerField()),
                ('page', models.ForeignKey(to='info.InfoPage')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AlterUniqueTogether(
            name='viewcount',
            unique_together=set([('date', 'page')]),
        ),
        migrations.AddField(
            model_name='infopage',
            name='tags',
            field=models.ManyToManyField(related_name='entries', to='info.Tag', blank=True),
            preserve_default=True,
        ),
    ]

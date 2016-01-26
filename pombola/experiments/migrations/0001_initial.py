# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Event',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('user_key', models.CharField(help_text=b'An identifier for a user, e.g. based on the session key', max_length=512)),
                ('variant', models.CharField(help_text=b'This identifies the page variant presented to the user', max_length=128)),
                ('category', models.CharField(help_text=b'Following GA, "Typically the object that was interacted with (e.g. button)"', max_length=128)),
                ('action', models.CharField(help_text=b'Following GA, "The type of interaction (e.g. click)"', max_length=128)),
                ('label', models.CharField(help_text=b'Following GA, "Useful for categorizing events (e.g. nav buttons)"', max_length=128)),
                ('extra_data', models.TextField(help_text=b'For arbitrary additional data, which should be valid JSON or empty', blank=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Experiment',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('slug', models.SlugField(unique=True)),
                ('name', models.CharField(max_length=300)),
                ('description', models.TextField(blank=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='event',
            name='experiment',
            field=models.ForeignKey(to='experiments.Experiment'),
            preserve_default=True,
        ),
    ]

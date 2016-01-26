# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import datetime


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='File',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(default=datetime.datetime.now, auto_now_add=True)),
                ('updated', models.DateTimeField(default=datetime.datetime.now, auto_now=True)),
                ('slug', models.SlugField(unique=True)),
                ('file', models.FileField(upload_to=b'file_archive')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]

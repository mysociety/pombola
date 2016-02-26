# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Task',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('object_id', models.PositiveIntegerField()),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('defer_until', models.DateTimeField(auto_now_add=True)),
                ('priority', models.PositiveIntegerField()),
                ('attempt_count', models.PositiveIntegerField(default=0)),
                ('log', models.TextField(blank=True)),
                ('note', models.TextField(blank=True)),
            ],
            options={
                'ordering': ['-priority', 'attempt_count', 'defer_until'],
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='TaskCategory',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('slug', models.SlugField(unique=True, max_length=100)),
                ('priority', models.PositiveIntegerField(default=0)),
            ],
            options={
                'ordering': ['-priority', 'slug'],
                'verbose_name_plural': 'Task categories',
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='task',
            name='category',
            field=models.ForeignKey(to='tasks.TaskCategory'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='task',
            name='content_type',
            field=models.ForeignKey(to='contenttypes.ContentType'),
            preserve_default=True,
        ),
    ]

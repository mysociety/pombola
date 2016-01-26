# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import datetime
import django_date_extensions.fields


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Budget',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(default=datetime.datetime.now, auto_now_add=True)),
                ('updated', models.DateTimeField(default=datetime.datetime.now, auto_now=True)),
                ('object_id', models.PositiveIntegerField()),
                ('organisation', models.CharField(max_length=150)),
                ('name', models.CharField(max_length=150)),
                ('currency', models.CharField(max_length=3)),
                ('value', models.IntegerField()),
                ('source_url', models.URLField(blank=True)),
                ('source_name', models.CharField(max_length=200, blank=True)),
            ],
            options={
                'ordering': ('-budget_session__date_start', 'budget_session__name', 'name'),
                'verbose_name_plural': 'budgets',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='BudgetSession',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(default=datetime.datetime.now, auto_now_add=True)),
                ('updated', models.DateTimeField(default=datetime.datetime.now, auto_now=True)),
                ('name', models.CharField(max_length=150)),
                ('date_start', django_date_extensions.fields.ApproximateDateField(max_length=10, blank=True)),
                ('date_end', django_date_extensions.fields.ApproximateDateField(max_length=10, blank=True)),
            ],
            options={
                'ordering': ('-date_start', 'name'),
                'verbose_name_plural': 'budget sessions',
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='budget',
            name='budget_session',
            field=models.ForeignKey(to='budgets.BudgetSession', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='budget',
            name='content_type',
            field=models.ForeignKey(to='contenttypes.ContentType'),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name='budget',
            unique_together=set([('content_type', 'object_id', 'name', 'budget_session')]),
        ),
    ]

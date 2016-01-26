# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import datetime
import django.contrib.gis.db.models.fields


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0002_add_related_name'),
    ]

    operations = [
        migrations.CreateModel(
            name='Project',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(default=datetime.datetime.now, auto_now_add=True)),
                ('updated', models.DateTimeField(default=datetime.datetime.now, auto_now=True)),
                ('cdf_index', models.IntegerField(unique=True)),
                ('project_name', models.CharField(max_length=400)),
                ('location_name', models.CharField(max_length=400)),
                ('sector', models.CharField(max_length=400)),
                ('mtfe_sector', models.CharField(max_length=400)),
                ('econ1', models.CharField(max_length=400)),
                ('econ2', models.CharField(max_length=400)),
                ('activity_to_be_done', models.CharField(max_length=400)),
                ('expected_output', models.CharField(max_length=400)),
                ('status', models.CharField(max_length=400)),
                ('remarks', models.CharField(max_length=400)),
                ('estimated_cost', models.FloatField()),
                ('total_cost', models.FloatField()),
                ('first_funding_year', models.IntegerField(null=True, blank=True)),
                ('location', django.contrib.gis.db.models.fields.PointField(srid=4326)),
                ('constituency', models.ForeignKey(to='core.Place')),
            ],
            options={
                'ordering': ['-total_cost'],
            },
            bases=(models.Model,),
        ),
    ]

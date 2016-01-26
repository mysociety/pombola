# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0002_add_related_name'),
    ]

    operations = [
        migrations.CreateModel(
            name='Entry',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('population_male', models.PositiveIntegerField()),
                ('population_female', models.PositiveIntegerField()),
                ('population_total', models.PositiveIntegerField()),
                ('population_rank', models.PositiveIntegerField(null=True)),
                ('gender_index', models.DecimalField(null=True, max_digits=7, decimal_places=6)),
                ('gender_index_rank', models.PositiveIntegerField(null=True)),
                ('households_total', models.PositiveIntegerField()),
                ('average_household_size', models.DecimalField(null=True, max_digits=5, decimal_places=3)),
                ('household_size_rank', models.PositiveIntegerField(null=True)),
                ('area', models.DecimalField(max_digits=10, decimal_places=2)),
                ('area_rank', models.PositiveIntegerField(null=True)),
                ('population_density', models.DecimalField(null=True, max_digits=9, decimal_places=2)),
                ('population_density_rank', models.PositiveIntegerField(null=True)),
                ('registered_voters_total', models.PositiveIntegerField(null=True)),
                ('registered_voters_proportion', models.DecimalField(null=True, max_digits=4, decimal_places=3)),
                ('registered_voters_proportion_rank', models.PositiveIntegerField(null=True)),
                ('youth_voters_proportion', models.DecimalField(null=True, max_digits=4, decimal_places=3)),
                ('youth_voters_proportion_rank', models.PositiveIntegerField(null=True)),
                ('place', models.OneToOneField(related_name='placedata', to='core.Place')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]

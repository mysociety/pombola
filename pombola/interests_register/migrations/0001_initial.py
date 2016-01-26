# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0002_add_related_name'),
    ]

    operations = [
        migrations.CreateModel(
            name='Category',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=300)),
                ('slug', models.SlugField(unique=True)),
                ('sort_order', models.IntegerField()),
            ],
            options={
                'ordering': ('sort_order', 'name'),
                'verbose_name_plural': 'categories',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Entry',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('sort_order', models.IntegerField()),
                ('category', models.ForeignKey(related_name='entries', to='interests_register.Category')),
                ('person', models.ForeignKey(related_name='interests_register_entries', to='core.Person')),
            ],
            options={
                'ordering': ('person__legal_name', '-release__date', 'category__sort_order', 'category__name', 'sort_order'),
                'verbose_name_plural': 'entries',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='EntryLineItem',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('key', models.CharField(max_length=240)),
                ('value', models.TextField()),
                ('entry', models.ForeignKey(related_name='line_items', to='interests_register.Entry')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Release',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=300)),
                ('slug', models.SlugField(unique=True)),
                ('date', models.DateField()),
            ],
            options={
                'ordering': ('date', 'name'),
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='entry',
            name='release',
            field=models.ForeignKey(related_name='entries', to='interests_register.Release'),
            preserve_default=True,
        ),
    ]

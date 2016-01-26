# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0002_add_related_name'),
    ]

    operations = [
        migrations.CreateModel(
            name='Bill',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('title', models.CharField(max_length=256)),
                ('source_url', models.URLField(unique=True)),
                ('act_title', models.CharField(max_length=256, null=True, blank=True)),
                ('act_source_url', models.URLField(unique=True, null=True, blank=True)),
                ('date', models.DateField()),
                ('parliamentary_session', models.ForeignKey(to='core.ParliamentarySession')),
                ('sponsor', models.ForeignKey(related_name='bills_sponsored', to='core.Person')),
            ],
            options={
                'ordering': ('date',),
            },
            bases=(models.Model,),
        ),
    ]

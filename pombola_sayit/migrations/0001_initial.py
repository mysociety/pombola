# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0002_add_related_name'),
        ('speeches', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='PombolaSayItJoin',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('pombola_person', models.OneToOneField(related_name='sayit_link', to='core.Person')),
                ('sayit_speaker', models.OneToOneField(related_name='pombola_link', to='speeches.Speaker')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]

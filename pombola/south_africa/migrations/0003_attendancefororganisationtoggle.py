# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0014_auto_20190906_1342'),
        ('south_africa', '0002_add_parliamentary_sessions'),
    ]

    operations = [
        migrations.CreateModel(
            name='AttendanceForOrganisationToggle',
            fields=[
            ],
            options={
                'verbose_name': 'Toggle attendance for party',
                'proxy': True,
                'verbose_name_plural': 'Toggle attendance for parties',
            },
            bases=('core.organisation',),
        ),
    ]

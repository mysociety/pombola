# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0002_add_related_name'),
    ]

    operations = [
        migrations.CreateModel(
            name='ZAPlace',
            fields=[
            ],
            options={
                'proxy': True,
            },
            bases=('core.place',),
        ),
    ]

# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0004_parliamentarysession_position_title'),
    ]

    operations = [
        migrations.AlterField(
            model_name='parliamentarysession',
            name='house',
            field=models.ForeignKey(blank=True, to='core.Organisation', null=True),
        ),
    ]

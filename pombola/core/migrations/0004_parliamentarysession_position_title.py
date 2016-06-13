# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0003_new_emailfield_max_length'),
    ]

    operations = [
        migrations.AddField(
            model_name='parliamentarysession',
            name='position_title',
            field=models.ForeignKey(blank=True, to='core.PositionTitle', null=True),
        ),
    ]

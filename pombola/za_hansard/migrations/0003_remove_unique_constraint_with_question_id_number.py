# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('za_hansard', '0002_add_pmg_api_fields'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='question',
            unique_together=set([('written_number', 'house', 'year'), ('dp_number', 'house', 'year'), ('oral_number', 'house', 'year'), ('president_number', 'house', 'year')]),
        ),
    ]

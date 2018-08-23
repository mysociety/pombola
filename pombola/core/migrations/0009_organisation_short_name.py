# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0008_sort_organisations_by_name'),
    ]

    operations = [
        migrations.AddField(
            model_name='organisation',
            name='short_name',
            field=models.CharField(max_length=200, null=True, editable=False),
        ),
    ]

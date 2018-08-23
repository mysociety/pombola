# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0010_organisation_update_short_name'),
    ]

    operations = [
        migrations.AlterField(
            model_name='organisation',
            name='short_name',
            field=models.CharField(max_length=200, editable=False),
        ),
    ]

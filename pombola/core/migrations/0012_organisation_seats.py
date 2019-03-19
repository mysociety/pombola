# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0011_organisation_alter_short_name'),
    ]

    operations = [
        migrations.AddField(
            model_name='organisation',
            name='seats',
            field=models.IntegerField(blank=True, help_text=b'The number of seats this organisation nominally has.', null=True, validators=[django.core.validators.MinValueValidator(1)]),
        ),
    ]

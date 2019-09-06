# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0013_organisation_show_attendance'),
    ]

    operations = [
        migrations.AlterField(
            model_name='organisation',
            name='show_attendance',
            field=models.BooleanField(default=False, help_text=b'Toggles attendance records on person detail pages for people who belong to this organization.'),
        ),
    ]

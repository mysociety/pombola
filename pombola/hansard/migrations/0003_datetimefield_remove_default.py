# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hansard', '0002_source_unique_together_constraint'),
    ]

    operations = [
        migrations.AlterField(
            model_name='alias',
            name='created',
            field=models.DateTimeField(auto_now_add=True),
        ),
        migrations.AlterField(
            model_name='alias',
            name='updated',
            field=models.DateTimeField(auto_now=True),
        ),
    ]

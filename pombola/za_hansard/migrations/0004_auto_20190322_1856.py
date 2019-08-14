# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('za_hansard', '0003_remove_unique_constraint_with_question_id_number'),
    ]

    operations = [
        migrations.AlterField(
            model_name='source',
            name='document_number',
            field=models.CharField(unique=True, max_length=200),
        ),
    ]

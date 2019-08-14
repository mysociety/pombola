# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('za_hansard', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='answer',
            name='pmg_api_url',
            field=models.URLField(max_length=1000, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='question',
            name='pmg_api_member_pa_url',
            field=models.URLField(max_length=1000, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='question',
            name='pmg_api_source_file_url',
            field=models.URLField(max_length=1000, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='question',
            name='pmg_api_url',
            field=models.URLField(max_length=1000, null=True, blank=True),
        ),
    ]

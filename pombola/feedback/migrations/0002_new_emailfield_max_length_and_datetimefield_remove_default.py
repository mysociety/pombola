# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('feedback', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='feedback',
            name='created',
            field=models.DateTimeField(auto_now_add=True),
        ),
        migrations.AlterField(
            model_name='feedback',
            name='email',
            field=models.EmailField(help_text=b'Please let us have your email address so that we can get back to you.', max_length=254, blank=True),
        ),
        migrations.AlterField(
            model_name='feedback',
            name='updated',
            field=models.DateTimeField(auto_now=True),
        ),
    ]

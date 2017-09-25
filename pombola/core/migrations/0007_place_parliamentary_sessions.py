# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0006_place_parliamentary_session_change_related_name'),
    ]

    operations = [
        migrations.AddField(
            model_name='place',
            name='parliamentary_sessions',
            field=models.ManyToManyField(to='core.ParliamentarySession'),
        ),
    ]

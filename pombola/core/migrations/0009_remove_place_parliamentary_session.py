# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0008_migrate_parliamentary_sessions'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='place',
            name='parliamentary_session',
        ),
    ]

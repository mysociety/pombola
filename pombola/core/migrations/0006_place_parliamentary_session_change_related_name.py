# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0005_parliamentarysession_make_house_optional'),
    ]

    operations = [
        migrations.AlterField(
            model_name='place',
            name='parliamentary_session',
            field=models.ForeignKey(related_name='old_parliamentary_session', blank=True, to='core.ParliamentarySession', null=True),
        ),
    ]

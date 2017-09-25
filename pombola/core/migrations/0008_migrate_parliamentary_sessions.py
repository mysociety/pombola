# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations


def migrate_to_m2m(apps, schema_editor):
    Place = apps.get_model('core', 'Place')
    for p in Place.objects.all():
        if p.parliamentary_session:
            p.parliamentary_sessions.add(p.parliamentary_session)


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0007_place_parliamentary_sessions'),
    ]

    operations = [
        migrations.RunPython(migrate_to_m2m),
    ]

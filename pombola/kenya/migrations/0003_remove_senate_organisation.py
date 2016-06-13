# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations


def remove_house_from_senate_session(apps, schema_editor):
    ParliamentarySession = apps.get_model('core', 'ParliamentarySession')
    try:
        ps = ParliamentarySession.objects.get(slug='s2013')
        ps.house = None
        ps.save()
    except ParliamentarySession.DoesNotExist:
        pass


def put_back_house_for_senate_session(apps, schema_editor):
    ParliamentarySession = apps.get_model('core', 'ParliamentarySession')
    Organisation = apps.get_model('core', 'Organisation')
    try:
        ps = ParliamentarySession.objects.get(slug='s2013')
        ps.house = Organisation.objects.get(slug='senate')
        ps.save()
    except ParliamentarySession.DoesNotExist:
        pass


class Migration(migrations.Migration):

    dependencies = [
        ('kenya', '0002_adjust_parliamentary_sessions'),
        ('core', '0005_parliamentarysession_make_house_optional'),
    ]

    operations = [
        migrations.RunPython(
            remove_house_from_senate_session,
            put_back_house_for_senate_session,
        )
    ]

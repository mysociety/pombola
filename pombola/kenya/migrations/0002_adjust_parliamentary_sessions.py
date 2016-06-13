# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations


def add_position_title(apps, schema_editor):
    ParliamentarySession = apps.get_model('core', 'ParliamentarySession')
    PositionTitle = apps.get_model('core', 'PositionTitle')
    for ps_slug, pt_slug in (
            ('na2007', 'mp'),
            ('na2013', 'member-national-assembly'),
            ('s2013', 'senator'),
    ):
        try:
            ps = ParliamentarySession.objects.get(slug=ps_slug)
            ps.position_title = PositionTitle.objects.get(slug=pt_slug)
            ps.save()
        except ParliamentarySession.DoesNotExist:
            pass


def remove_position_title(apps, schema_editor):
    ParliamentarySession = apps.get_model('core', 'ParliamentarySession')
    for ps_slug in ('na2007', 'na2013', 's2013'):
        try:
            ps = ParliamentarySession.objects.get(slug=ps_slug)
            ps.position_title = None
            ps.save()
        except ParliamentarySession.DoesNotExist:
            pass


class Migration(migrations.Migration):

    dependencies = [
        ('kenya', '0001_fix_mapit_area_types'),
        ('core', '0005_parliamentarysession_make_house_optional'),
    ]

    operations = [
        migrations.RunPython(
            add_position_title,
            remove_position_title,
        )
    ]

# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations


def add_parliamentary_sessions(apps, schema_editor):
    ParliamentarySession = apps.get_model('core', 'ParliamentarySession')
    Organisation = apps.get_model('core', 'Organisation')
    PositionTitle = apps.get_model('core', 'PositionTitle')
    # National Assembly:
    if Organisation.objects.filter(slug='national-assembly').exists():
        #   Current:
        ParliamentarySession.objects.create(
            start_date='2014-05-21',
            end_date='2019-05-21',
            house=Organisation.objects.get(slug='national-assembly'),
            position_title=PositionTitle.objects.get(slug='member'),
            mapit_generation=1,
            name='26th Parliament (National Assembly)',
            slug='na26',
        )
        #   Previous:
        ParliamentarySession.objects.create(
            start_date='2009-05-06',
            end_date='2014-05-06',
            house=Organisation.objects.get(slug='national-assembly'),
            position_title=PositionTitle.objects.get(slug='member'),
            mapit_generation=1,
            name='25th Parliament (National Assembly)',
            slug='na25',
        )
    if Organisation.objects.filter(slug='ncop').exists():
        # NCOP:
        #   Current:
        ParliamentarySession.objects.create(
            start_date='2014-05-21',
            end_date='2019-05-21',
            house=Organisation.objects.get(slug='ncop'),
            position_title=PositionTitle.objects.get(slug='delegate'),
            mapit_generation=1,
            name='26th Parliament (National Council of Provinces)',
            slug='ncop26',
        )
        #   Previous:
        ParliamentarySession.objects.create(
            start_date='2009-05-06',
            end_date='2014-05-06',
            house=Organisation.objects.get(slug='ncop'),
            position_title=PositionTitle.objects.get(slug='delegate'),
            mapit_generation=1,
            name='25th Parliament (National Council of Provinces)',
            slug='ncop25',
        )


def remove_parliamentary_sessions(apps, schema_editor):
    ParliamentarySession = apps.get_model('core', 'ParliamentarySession')
    ParliamentarySession.objects.filter(
        slug__in=('na25', 'na26', 'ncop25', 'ncop26')
    ).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0001_initial'),
        ('south_africa', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(
            add_parliamentary_sessions,
            remove_parliamentary_sessions,
        ),
    ]

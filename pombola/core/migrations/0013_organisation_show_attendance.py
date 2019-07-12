# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings

def show_attendance_true_for_major_za_parties(apps, schema_editor):
    if settings.COUNTRY_APP == 'south_africa':
        Organisation = apps.get_model('core', 'Organisation')
        parties = Organisation.objects.filter(kind__slug='party')

        for party in parties:
            if party.slug in ['anc', 'da', 'eff']:
                party.show_attendance = True
                party.save()

class Migration(migrations.Migration):

    dependencies = [
        ('core', '0012_organisation_seats'),
    ]

    operations = [
        migrations.AddField(
            model_name='organisation',
            name='show_attendance',
            field=models.BooleanField(default=False),
        ),
        migrations.RunPython(show_attendance_true_for_major_za_parties)
    ]

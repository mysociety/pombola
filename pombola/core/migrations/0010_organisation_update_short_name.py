# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import re


def shorten_name(name):

    strip_phrases = [
        'Portfolio Committee on',
        'Standing Committee on',
    ]

    for phrase in strip_phrases:
        name = re.sub('(?i)' + re.escape(phrase), '', name)

    return name.strip()


def resave_organisations(apps, schema_editor):
    Organisation = apps.get_model('core', 'Organisation')
    organisations = Organisation.objects.all()

    for organisation in organisations:
        organisation.short_name = shorten_name(organisation.name)
        organisation.save()


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0009_organisation_short_name'),
    ]

    operations = [
        migrations.RunPython(resave_organisations),
    ]

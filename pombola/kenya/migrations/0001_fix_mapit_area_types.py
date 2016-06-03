# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations

def uppercase_type_names(apps, schema_editor):
    Type = apps.get_model('mapit', 'Type')
    for mapit_type in Type.objects.all():
        new_code = mapit_type.code.upper()
        mapit_type.code = new_code
        mapit_type.save()

def lowercase_type_names(apps, schema_editor):
    Type = apps.get_model('mapit', 'Type')
    for mapit_type in Type.objects.all():
        new_code = mapit_type.code.lower()
        mapit_type.code = new_code
        mapit_type.save()


class Migration(migrations.Migration):

    dependencies = [
        ('mapit', '0002_auto_20141218_1615'),
    ]

    operations = [
        migrations.RunPython(
            uppercase_type_names,
            lowercase_type_names,
        )
    ]

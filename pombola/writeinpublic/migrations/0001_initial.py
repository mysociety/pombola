# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Configuration',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('url', models.CharField(help_text=b'URL for the WriteInPublic API without instance subdomain, e.g. http://writeinpublic.pa.org.za', max_length=200)),
                ('instance_id', models.PositiveIntegerField(help_text=b'Instance ID, can be found at /en/manage/settings/api/ on your instance subdomain')),
                ('username', models.CharField(help_text=b'Username for the WriteInPublic instance you want to use', max_length=30)),
                ('api_key', models.CharField(help_text=b'API key for the WriteInPublic instance you want to use', max_length=128)),
                ('slug', models.CharField(help_text=b'A unique human-friendly identifier for this configuration', unique=True, max_length=30)),
                ('person_uuid_prefix', models.CharField(help_text=b"The prefix for people's UUID", max_length=200)),
            ],
        ),
    ]

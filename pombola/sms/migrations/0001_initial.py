# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Message',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('status', models.CharField(default=b'pending', max_length=10, choices=[(b'pending', b'Pending'), (b'accepted', b'Accepted'), (b'rejected', b'Rejected')])),
                ('text', models.TextField()),
                ('msisdn', models.TextField()),
                ('datetime', models.DateTimeField()),
            ],
        ),
        migrations.AlterUniqueTogether(
            name='message',
            unique_together=set([('text', 'msisdn', 'datetime')]),
        ),
    ]

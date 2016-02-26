# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import datetime
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Feedback',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(default=datetime.datetime.now, auto_now_add=True)),
                ('updated', models.DateTimeField(default=datetime.datetime.now, auto_now=True)),
                ('email', models.EmailField(help_text=b'Please let us have your email address so that we can get back to you.', max_length=75, blank=True)),
                ('url', models.URLField(blank=True)),
                ('comment', models.CharField(max_length=2000)),
                ('status', models.CharField(default=b'pending', max_length=20, choices=[(b'pending', b'Pending'), (b'rejected', b'Rejected'), (b'applied', b'Applied'), (b'non-actionable', b'Non-actionable'), (b'spammy', b'Possible Spam')])),
                ('response', models.TextField(blank=True)),
                ('user', models.ForeignKey(blank=True, to=settings.AUTH_USER_MODEL, null=True)),
            ],
            options={
                'ordering': ['created'],
                'verbose_name_plural': 'feedback',
            },
            bases=(models.Model,),
        ),
    ]

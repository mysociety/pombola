# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0006_add_role_responsibilities'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='contact',
            options={'ordering': ['content_type', '-preferred', 'object_id', 'kind']},
        ),
        migrations.AddField(
            model_name='contact',
            name='preferred',
            field=models.BooleanField(default=False, help_text=b'Should this contact detail be listed before others of the same type?'),
            preserve_default=False,
        ),
    ]

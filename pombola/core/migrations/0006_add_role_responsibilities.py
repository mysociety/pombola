# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import markitup.fields


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0005_parliamentarysession_make_house_optional'),
    ]

    operations = [
        migrations.AddField(
            model_name='positiontitle',
            name='_responsibilities_rendered',
            field=models.TextField(editable=False, blank=True),
        ),
        migrations.AddField(
            model_name='positiontitle',
            name='responsibilities',
            field=markitup.fields.MarkupField(default=b'', no_rendered_field=True, blank=True),
        ),
    ]

# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import markitup.fields
import django.utils.timezone
import pombola.votematch.models
import model_utils.fields


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Answer',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, verbose_name='created', editable=False)),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, verbose_name='modified', editable=False)),
                ('agreement', models.IntegerField(choices=[(-2, b'strongly disagree'), (-1, b'disagree'), (0, b'neutral'), (1, b'agree'), (2, b'strongly agree')])),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Party',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, verbose_name='created', editable=False)),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, verbose_name='modified', editable=False)),
                ('name', models.TextField()),
                ('url', models.URLField(null=True, blank=True)),
                ('summary', markitup.fields.MarkupField(no_rendered_field=True, blank=True)),
                ('_summary_rendered', models.TextField(editable=False, blank=True)),
            ],
            options={
                'verbose_name_plural': 'parties',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Quiz',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, verbose_name='created', editable=False)),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, verbose_name='modified', editable=False)),
                ('name', models.TextField(unique=True)),
                ('slug', models.SlugField(help_text=b'created from name', unique=True, max_length=200)),
            ],
            options={
                'verbose_name_plural': 'quizzes',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Stance',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, verbose_name='created', editable=False)),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, verbose_name='modified', editable=False)),
                ('agreement', models.IntegerField(choices=[(-2, b'strongly disagree'), (-1, b'disagree'), (0, b'neutral'), (1, b'agree'), (2, b'strongly agree')])),
                ('party', models.ForeignKey(to='votematch.Party')),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Statement',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, verbose_name='created', editable=False)),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, verbose_name='modified', editable=False)),
                ('text', models.TextField()),
                ('quiz', models.ForeignKey(to='votematch.Quiz')),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Submission',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, verbose_name='created', editable=False)),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, verbose_name='modified', editable=False)),
                ('token', models.TextField(default=pombola.votematch.models.generate_token, unique=True)),
                ('age', models.PositiveIntegerField(null=True, blank=True)),
                ('expected_result', models.ForeignKey(blank=True, to='votematch.Party', null=True)),
                ('quiz', models.ForeignKey(to='votematch.Quiz')),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='stance',
            name='statement',
            field=models.ForeignKey(to='votematch.Statement'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='party',
            name='quiz',
            field=models.ForeignKey(to='votematch.Quiz'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='answer',
            name='statement',
            field=models.ForeignKey(to='votematch.Statement'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='answer',
            name='submission',
            field=models.ForeignKey(to='votematch.Submission'),
            preserve_default=True,
        ),
    ]

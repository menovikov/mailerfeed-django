# -*- coding: utf-8 -*-
# Generated by Django 1.9 on 2017-11-21 22:41
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('common', '0010_umailing_read_state_update'),
    ]

    operations = [
        migrations.AlterField(
            model_name='umailing',
            name='read_state_update',
            field=models.IntegerField(choices=[(1, 'Updating is required'), (2, 'Updating state is completed')], default=1),
        ),
    ]

# -*- coding: utf-8 -*-
# Generated by Django 1.9 on 2017-11-23 19:16
from __future__ import unicode_literals

import datetime
from django.db import migrations, models
from django.utils.timezone import utc


class Migration(migrations.Migration):

    dependencies = [
        ('linker', '0005_auto_20171123_1645'),
    ]

    operations = [
        migrations.AlterField(
            model_name='linkclick',
            name='date',
            field=models.DateTimeField(default=datetime.datetime(2017, 11, 23, 19, 16, 55, 164224, tzinfo=utc)),
        ),
    ]

# -*- coding: utf-8 -*-
# Generated by Django 1.9 on 2017-11-19 12:20
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tgconnector', '0002_tgmessage_sid'),
    ]

    operations = [
        migrations.AddField(
            model_name='tgmessage',
            name='status',
            field=models.IntegerField(default=0),
        ),
    ]

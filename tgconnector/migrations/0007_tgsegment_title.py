# -*- coding: utf-8 -*-
# Generated by Django 1.9 on 2017-12-18 22:30
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tgconnector', '0006_auto_20171210_1743'),
    ]

    operations = [
        migrations.AddField(
            model_name='tgsegment',
            name='title',
            field=models.CharField(max_length=128, null=True),
        ),
    ]

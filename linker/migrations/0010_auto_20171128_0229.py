# -*- coding: utf-8 -*-
# Generated by Django 1.9 on 2017-11-27 23:29
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('linker', '0009_auto_20171128_0124'),
    ]

    operations = [
        migrations.AlterField(
            model_name='linkclick',
            name='date',
            field=models.DateTimeField(auto_now_add=True),
        ),
    ]

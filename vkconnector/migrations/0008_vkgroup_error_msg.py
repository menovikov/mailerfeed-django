# -*- coding: utf-8 -*-
# Generated by Django 1.9 on 2017-11-19 19:38
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('vkconnector', '0007_vkmessage_status'),
    ]

    operations = [
        migrations.AddField(
            model_name='vkgroup',
            name='error_msg',
            field=models.TextField(blank=True, null=True),
        ),
    ]

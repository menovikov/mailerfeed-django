# -*- coding: utf-8 -*-
# Generated by Django 1.9 on 2017-11-12 22:31
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('common', '0005_profile_tg_id'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='tg_phone_code_hash',
            field=models.CharField(max_length=256, null=True),
        ),
    ]
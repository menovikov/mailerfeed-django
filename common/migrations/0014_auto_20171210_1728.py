# -*- coding: utf-8 -*-
# Generated by Django 1.9 on 2017-12-10 14:28
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('common', '0013_umailing_title'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='umailing',
            options={'ordering': ('-id',)},
        ),
    ]
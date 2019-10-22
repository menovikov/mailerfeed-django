# -*- coding: utf-8 -*-
# Generated by Django 1.9 on 2017-11-27 23:42
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('triggers', '0004_auto_20171128_0233'),
    ]

    operations = [
        migrations.AddField(
            model_name='triggerchainitem',
            name='text',
            field=models.TextField(default='Empty message'),
        ),
        migrations.AddField(
            model_name='triggerchainitem',
            name='title',
            field=models.CharField(default='Unnamed', max_length=256),
        ),
        migrations.AddField(
            model_name='triggerchainitem',
            name='type',
            field=models.IntegerField(default=1),
        ),
        migrations.AlterField(
            model_name='trigger',
            name='title',
            field=models.CharField(default='Unnamed', max_length=256),
        ),
    ]
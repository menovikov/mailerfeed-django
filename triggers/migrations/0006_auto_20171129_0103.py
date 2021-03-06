# -*- coding: utf-8 -*-
# Generated by Django 1.9 on 2017-11-28 22:03
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('triggers', '0005_auto_20171128_0242'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='triggerchainitem',
            options={'ordering': ('trigger', 'position')},
        ),
        migrations.AddField(
            model_name='triggerchainitem',
            name='position',
            field=models.IntegerField(default=0),
            preserve_default=False,
        ),
        migrations.RemoveField(
            model_name='triggerchainitem',
            name='right',
        ),
        migrations.AlterUniqueTogether(
            name='triggerchainitem',
            unique_together=set([('trigger', 'position')]),
        ),
    ]

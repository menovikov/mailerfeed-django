# -*- coding: utf-8 -*-
# Generated by Django 1.9 on 2017-12-10 14:43
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tgconnector', '0005_auto_20171122_0141'),
    ]

    operations = [
        migrations.AlterField(
            model_name='tgmailing',
            name='network',
            field=models.PositiveIntegerField(choices=[(1, 'vk.com'), (2, 'telegram.com')]),
        ),
        migrations.AlterField(
            model_name='tgmessage',
            name='network',
            field=models.PositiveIntegerField(choices=[(1, 'vk.com'), (2, 'telegram.com')]),
        ),
        migrations.AlterField(
            model_name='tgsegment',
            name='network',
            field=models.PositiveIntegerField(choices=[(1, 'vk.com'), (2, 'telegram.com')]),
        ),
        migrations.AlterField(
            model_name='tguser',
            name='network',
            field=models.PositiveIntegerField(choices=[(1, 'vk.com'), (2, 'telegram.com')]),
        ),
    ]

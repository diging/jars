# -*- coding: utf-8 -*-
# Generated by Django 1.9.6 on 2017-05-19 15:57
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('cookies', '0013_datasetsnapshot_state'),
    ]

    operations = [
        migrations.AlterField(
            model_name='datasetsnapshot',
            name='resource',
            field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='snapshot', to='cookies.Resource'),
        ),
    ]

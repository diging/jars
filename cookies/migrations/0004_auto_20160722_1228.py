# -*- coding: utf-8 -*-
# Generated by Django 1.9.8 on 2016-07-22 12:28
from __future__ import unicode_literals

import datetime
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
from django.utils.timezone import utc


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('cookies', '0003_auto_20160722_1155'),
    ]

    operations = [
        migrations.AddField(
            model_name='collection',
            name='created',
            field=models.DateTimeField(auto_now_add=True, default=datetime.datetime(2016, 7, 22, 12, 28, 15, 472006, tzinfo=utc)),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='collection',
            name='created_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='conceptentity',
            name='created',
            field=models.DateTimeField(auto_now_add=True, default=datetime.datetime(2016, 7, 22, 12, 28, 26, 918173, tzinfo=utc)),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='conceptentity',
            name='created_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='relation',
            name='created',
            field=models.DateTimeField(auto_now_add=True, default=datetime.datetime(2016, 7, 22, 12, 28, 29, 69179, tzinfo=utc)),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='relation',
            name='created_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='resource',
            name='created',
            field=models.DateTimeField(auto_now_add=True, default=datetime.datetime(2016, 7, 22, 12, 28, 30, 187159, tzinfo=utc)),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='resource',
            name='created_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
    ]
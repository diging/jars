# -*- coding: utf-8 -*-
# Generated by Django 1.9.8 on 2016-07-22 14:51
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('cookies', '0004_auto_20160722_1228'),
    ]

    operations = [
        migrations.CreateModel(
            name='UserJob',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('result_id', models.CharField(max_length=255)),
                ('result', models.TextField()),
                ('created_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='jobs', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]

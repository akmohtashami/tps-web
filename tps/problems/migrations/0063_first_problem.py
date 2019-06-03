# -*- coding: utf-8 -*-
# Generated by Django 1.9.7 on 2017-01-13 14:14
from __future__ import unicode_literals

from django.contrib.auth import get_user_model
from django.db import migrations


def create_base_problem(apps, schema_editor):
    pass


class Migration(migrations.Migration):
    dependencies = [
        ('problems', '0062_problemdata_statement'),
        ('accounts', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(create_base_problem, migrations.RunPython.noop)
    ]
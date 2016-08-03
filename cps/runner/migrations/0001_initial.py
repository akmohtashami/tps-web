# -*- coding: utf-8 -*-
# Generated by Django 1.9.7 on 2016-08-01 20:51
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion
import runner.runnable


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('file_repository', '0003_delete_file'),
    ]

    operations = [
        migrations.CreateModel(
            name='JobFile',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('filename', models.CharField(max_length=100)),
                ('type', models.CharField(choices=[('exec', 'executable'), ('r', 'read'), ('w', 'write'), ('extract', 'extracted')], max_length=20)),
                ('file_model', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='file_repository.FileModel')),
            ],
        ),
        migrations.CreateModel(
            name='JobModel',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('command', models.CharField(max_length=100)),
                ('stdin_filename', models.CharField(blank=True, max_length=100)),
                ('stdout_filename', models.CharField(blank=True, max_length=100)),
                ('stderr_filename', models.CharField(blank=True, max_length=100)),
                ('time_limit', models.FloatField(default=1)),
                ('memory_limit', models.IntegerField(default=131072)),
                ('description', models.CharField(blank=True, max_length=20)),
                ('execution_time', models.FloatField(blank=True)),
                ('execution_memory', models.IntegerField(blank=True)),
                ('success', models.BooleanField()),
                ('exit_status', models.CharField(blank=True, max_length=20)),
                ('exit_code', models.IntegerField(blank=True, null=True)),
                ('files', models.ManyToManyField(through='runner.JobFile', to='file_repository.FileModel')),
            ],
            bases=(runner.runnable.Runnable, models.Model),
        ),
        migrations.AddField(
            model_name='jobfile',
            name='job_model',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='runner.JobModel'),
        ),
    ]

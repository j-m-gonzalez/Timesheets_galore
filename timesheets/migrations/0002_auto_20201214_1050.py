# Generated by Django 3.1.2 on 2020-12-14 18:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('timesheets', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='clockpunch',
            options={'verbose_name_plural': 'clockpunches'},
        ),
        migrations.RemoveField(
            model_name='clockpunch',
            name='clock_in',
        ),
        migrations.AddField(
            model_name='clockpunch',
            name='clock',
            field=models.BooleanField(choices=[(True, 'Clock in'), (False, 'Clock out')], default=True),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='clockpunch',
            name='time',
            field=models.DateTimeField(blank=True),
        ),
    ]

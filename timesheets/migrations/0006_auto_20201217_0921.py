# Generated by Django 3.1.2 on 2020-12-17 17:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('timesheets', '0005_clockpunch_date_time'),
    ]

    operations = [
        migrations.AlterField(
            model_name='clockpunch',
            name='date_time',
            field=models.DateTimeField(auto_now_add=True),
        ),
    ]

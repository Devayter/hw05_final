# Generated by Django 2.2.16 on 2023-04-08 20:02

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0012_auto_20230408_2258'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='comment',
            name='сreated',
        ),
        migrations.AddField(
            model_name='comment',
            name='pub_date',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now, verbose_name='Дата публикации'),
            preserve_default=False,
        ),
    ]

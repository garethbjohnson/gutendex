# Generated by Django 4.0.2 on 2022-02-26 02:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('books', '0003_auto_20210302_2022'),
    ]

    operations = [
        migrations.AlterField(
            model_name='book',
            name='copyright',
            field=models.BooleanField(default=1),
            preserve_default=False,
        ),
    ]

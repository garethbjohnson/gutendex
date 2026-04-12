from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('books', '0008_rename_marc908_fields'),
    ]

    operations = [
        migrations.AddField(
            model_name='person',
            name='gutenberg_id',
            field=models.PositiveIntegerField(blank=True, null=True, unique=True),
        ),
    ]

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('books', '0005_book_editors'),
    ]

    operations = [
        migrations.AddField(
            model_name='book',
            name='published_year',
            field=models.SmallIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='book',
            name='wikipedia_url',
            field=models.URLField(blank=True, default='', max_length=512),
        ),
    ]

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('books', '0006_book_published_year_wikipedia_url'),
    ]

    operations = [
        migrations.AddField(
            model_name='book',
            name='marc908',
            field=models.CharField(blank=True, default='', max_length=256),
        ),
        migrations.AddField(
            model_name='book',
            name='marc908_score',
            field=models.FloatField(blank=True, null=True),
        ),
    ]

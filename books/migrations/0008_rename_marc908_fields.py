from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('books', '0007_book_marc908'),
    ]

    operations = [
        migrations.RenameField(
            model_name='book',
            old_name='marc908',
            new_name='reading_score',
        ),
        migrations.RenameField(
            model_name='book',
            old_name='marc908_score',
            new_name='reading_score_value',
        ),
    ]

# Generated by Django 5.1.3 on 2025-07-07 07:48

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('lexicon', '0016_lexiconentry_affixes'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='lexiconproject',
            options={'permissions': [('edit_lexiconproject', 'Can edit this lexicon project')]},
        ),
    ]

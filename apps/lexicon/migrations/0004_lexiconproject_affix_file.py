# Generated by Django 5.1.3 on 2024-12-01 06:09

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("lexicon", "0003_alter_lexiconproject_version"),
    ]

    operations = [
        migrations.AddField(
            model_name="lexiconproject",
            name="affix_file",
            field=models.TextField(
                default="# Hunspell affix file for Kovol by NTMPNG\nSET UTF-8\nTRY aeiouAEIOUpbtdkgjmnfsvhlrwyPBTDKGJMNFSVHLRWY\nWORDCHARS -\n\nNOSUGGEST !",
                help_text="See https://www.systutorials.com/docs/linux/man/4-hunspell/",
            ),
        ),
    ]

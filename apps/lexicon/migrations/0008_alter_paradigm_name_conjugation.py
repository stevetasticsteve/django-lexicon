# Generated by Django 5.1.3 on 2025-05-18 09:06

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lexicon', '0007_paradigm'),
    ]

    operations = [
        migrations.AlterField(
            model_name='paradigm',
            name='name',
            field=models.CharField(max_length=40),
        ),
        migrations.CreateModel(
            name='Conjugation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('row', models.IntegerField()),
                ('column', models.IntegerField()),
                ('conjugation', models.CharField(max_length=40)),
                ('paradigm', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='lexicon.paradigm')),
                ('word', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='lexicon.lexiconentry')),
            ],
        ),
    ]

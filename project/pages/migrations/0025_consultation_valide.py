# Generated by Django 5.1.3 on 2024-12-31 16:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pages', '0024_alter_consultation_id_facture'),
    ]

    operations = [
        migrations.AddField(
            model_name='consultation',
            name='valide',
            field=models.BooleanField(default=False),
        ),
    ]

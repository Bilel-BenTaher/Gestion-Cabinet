# Generated by Django 5.1.3 on 2025-01-02 12:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pages', '0036_rename_medicament_certificat_contenu_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='certificat',
            name='date',
            field=models.DateField(),
        ),
    ]

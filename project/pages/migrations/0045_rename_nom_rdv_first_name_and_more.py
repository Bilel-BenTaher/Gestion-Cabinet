# Generated by Django 5.1.3 on 2025-01-03 15:10

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('pages', '0044_rdv_nom_rdv_prénom'),
    ]

    operations = [
        migrations.RenameField(
            model_name='rdv',
            old_name='nom',
            new_name='first_name',
        ),
        migrations.RenameField(
            model_name='rdv',
            old_name='prénom',
            new_name='last_name',
        ),
    ]

# Generated by Django 5.1.3 on 2024-12-31 14:54

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('pages', '0021_alter_rdv_id_fiche_alter_rdv_id_patient'),
    ]

    operations = [
        migrations.RenameField(
            model_name='rdv',
            old_name='id_fiche',
            new_name='fiche',
        ),
    ]

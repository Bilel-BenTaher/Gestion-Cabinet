# Generated by Django 5.1.3 on 2025-01-06 16:37

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('pages', '0053_alter_rdv_options'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='rdv',
            options={'ordering': ['id_patient__username', 'id_patient__first_name']},
        ),
    ]

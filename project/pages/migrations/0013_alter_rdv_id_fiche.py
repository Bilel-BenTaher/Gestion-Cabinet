# Generated by Django 5.1.3 on 2024-12-31 11:30

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pages', '0012_alter_rdv_id_fiche'),
    ]

    operations = [
        migrations.AlterField(
            model_name='rdv',
            name='id_fiche',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='cons_fact', to='pages.fichepatient'),
        ),
    ]

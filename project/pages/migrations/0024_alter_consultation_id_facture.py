# Generated by Django 5.1.3 on 2024-12-31 15:40

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pages', '0023_fichepatient_valide'),
    ]

    operations = [
        migrations.AlterField(
            model_name='consultation',
            name='id_facture',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='cons_fact', to='pages.facture'),
        ),
    ]

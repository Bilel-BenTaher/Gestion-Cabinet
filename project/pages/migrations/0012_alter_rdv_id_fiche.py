# Generated by Django 5.1.3 on 2024-12-31 11:24

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pages', '0011_remove_rdv_id_secretaire_rdv_id_fiche'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AlterField(
            model_name='rdv',
            name='id_fiche',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='cons_fact', to=settings.AUTH_USER_MODEL),
        ),
    ]

# Generated by Django 5.1.1 on 2024-10-22 15:30

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('consultorioCys', '0003_cita'),
    ]

    operations = [
        migrations.AddField(
            model_name='informe',
            name='clinica',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='consultorioCys.clinica'),
        ),
        migrations.AddField(
            model_name='informe',
            name='sede',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='consultorioCys.sedeclinica'),
        ),
    ]

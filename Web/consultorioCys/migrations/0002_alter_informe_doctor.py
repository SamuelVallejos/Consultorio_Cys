# Generated by Django 5.1.1 on 2024-12-09 14:11

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('consultorioCys', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='informe',
            name='doctor',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='consultorioCys.doctor'),
        ),
    ]

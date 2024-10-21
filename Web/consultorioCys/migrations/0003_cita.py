# Generated by Django 5.1.1 on 2024-10-21 20:12

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('consultorioCys', '0002_paciente_archivo'),
    ]

    operations = [
        migrations.CreateModel(
            name='Cita',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('fecha_cita', models.DateField()),
                ('tratamiento', models.CharField(max_length=100)),
                ('confirmado', models.BooleanField(default=False)),
                ('doctor', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='consultorioCys.doctor')),
                ('paciente', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='consultorioCys.paciente')),
            ],
        ),
    ]

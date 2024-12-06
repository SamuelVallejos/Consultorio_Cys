# Generated by Django 5.1.1 on 2024-12-06 04:39

import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('consultorioCys', '0004_plan_alter_informe_descripcion_informe_suscripcion'),
    ]

    operations = [
        migrations.CreateModel(
            name='MetodoPago',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('tarjeta_numero', models.CharField(max_length=16)),
                ('tarjeta_tipo', models.CharField(max_length=20)),
                ('vencimiento', models.DateField()),
                ('creado_en', models.DateTimeField(default=django.utils.timezone.now)),
                ('usuario', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]

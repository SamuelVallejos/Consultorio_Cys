from django.db import models

class Sitio(models.Model):
    id_sitio = models.AutoField(primary_key=True)
    nombre_sitio = models.CharField(max_length=100)

    def __str__(self):
        return self.nombre_sitio

class Doctor(models.Model):
    id_doctor = models.AutoField(primary_key=True)
    nombre_completo = models.CharField(max_length=100)
    area_desempeño = models.CharField(max_length=100)
    fec_nac = models.DateField()
    num_telefono = models.CharField(max_length=15)  # Limit to 15 characters for phone numbers
    sitio = models.ForeignKey(Sitio, on_delete=models.CASCADE)  # Use ForeignKey for relational integrity
    
    class Meta:
        unique_together = (('id_doctor', 'sitio'),)
    
    def __str__(self):
        return self.nombre_completo

class Informe(models.Model):
    id_informe = models.AutoField(primary_key=True)
    nombre_completo_pac = models.CharField(max_length=200)
    tipo_servicio = models.TextField()
    medico_designado = models.CharField(max_length=100)
    resultados_pac = models.TextField()
    tratamiento = models.CharField(max_length=300)
    foto_pac = models.ImageField(upload_to='fotos_pacientes/')
    archivo_informe = models.FileField(upload_to='archivos_informes/')  # Use FileField for general file uploads
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='informes')
    
    def __str__(self):
        return f"Informe de {self.nombre_completo_pac}"

class Paciente(models.Model):
    id_paciente = models.AutoField(primary_key=True)
    nom_completo_pac = models.CharField(max_length=100)
    fecha_nac = models.DateField()
    genero = models.CharField(max_length=20)
    huella_dactilar = models.ImageField(upload_to='huellas_dactilares/')
    email = models.EmailField(max_length=100)
    direccion = models.CharField(max_length=100)
    
    def __str__(self):
        return self.nom_completo_pac

class PacienteServicio(models.Model):
    id_paciente_servicio = models.AutoField(primary_key=True)
    descripcion = models.CharField(max_length=200)
    
    def __str__(self):
        return self.descripcion


class Consultorio(models.Model):
    id_consultorio = models.AutoField(primary_key=True)
    region_con = models.CharField(max_length=30)
    comuna_con = models.CharField(max_length=30)
    direccion_con = models.CharField(max_length=100)

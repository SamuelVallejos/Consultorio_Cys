from django.db import models


class Doctor(models.Model):
    id_doctor = models.AutoField(primary_key=True)
    nombre_completo = models.CharField(max_length=100)
    area_desempeño = models.CharField(max_length=100)
    fec_nac = models.DateField()
    num_telefono = models.CharField(max_length=100)
    sitio_id_sitio = models.IntegerField() 
    
    class Meta:
        unique_together = (('id_doctor', 'sitio_id_sitio'),) 
    
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
    archivo_informe = models.ImageField(upload_to='archivos_informes/')
    doctor_id_doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='informes')
    
    def __str__(self):
        return f"Informe de {self.nombre_completo_pac}"
    
class Paciente(models.Model):
    id_paciente = models.AutoField(primary_key=True)
    nom_completo_pac = models.CharField(max_length=100)
    informe = models.CharField(max_length=300)  
    fecha_nac = models.DateField()
    genero = models.CharField(max_length=100)
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
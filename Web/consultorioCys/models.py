from django.db import models

class Administrador(models.Model):
    rut_administrador = models.CharField(max_length=10, primary_key=True, default='12345678-9')  # ID (Rut) Administrador
    nombres_administrador = models.CharField(max_length=100, default='Nombre Admin')  # Nombre/s Administrador
    primer_apellido_administrador = models.CharField(max_length=50, default='ApellidoAdmin')  # Primer Apellido Administrador
    segundo_apellido_administrador = models.CharField(max_length=50, blank=True, default='')  # Segundo Apellido Administrador
    correo_administrador = models.EmailField(max_length=100, default='admin@ejemplo.com')  # Correo Administrador
    telefono_administrador = models.CharField(max_length=15, default='1234567890')  # N° Teléfono Administrador

    def __str__(self):
        return f"{self.nombres_administrador} {self.primer_apellido_administrador}"

class Doctor(models.Model):
    rut_doctor = models.CharField(max_length=10, primary_key=True, default='98765432-1')  # ID (Rut) Doctor
    nombres_doctor = models.CharField(max_length=100, default='Nombre Doctor')  # Nombre/s Doctor
    primer_apellido_doctor = models.CharField(max_length=50, default='ApellidoDoctor')  # Primer Apellido Doctor
    segundo_apellido_doctor = models.CharField(max_length=50, blank=True, default='')  # Segundo Apellido Doctor
    correo_doctor = models.EmailField(max_length=100, default='doctor@ejemplo.com')  # Correo Doctor
    telefono_doctor = models.CharField(max_length=15, default='1234567890')  # N° Teléfono Doctor
    fecha_nacimiento_doctor = models.DateField(default='2000-01-01')  # Fecha de Nacimiento Doctor
    especialidad_doctor = models.CharField(max_length=100, default='Medicina General')  # Especialidad Doctor

    def __str__(self):
        return f"Dr. {self.nombres_doctor} {self.primer_apellido_doctor}"

class Paciente(models.Model):
    rut_paciente = models.CharField(max_length=10,primary_key=True ,default='12345678-9')  # ID (Rut) Paciente
    nombres_paciente = models.CharField(max_length=100, default='Nombre Paciente')  # Nombre/s Paciente
    primer_apellido_paciente = models.CharField(max_length=50, default='ApellidoPaciente')  # Primer Apellido Paciente
    segundo_apellido_paciente = models.CharField(max_length=50, blank=True, default='')  # Segundo Apellido Paciente
    correo_paciente = models.EmailField(max_length=100, default='paciente@ejemplo.com')  # Correo Paciente
    telefono_paciente = models.CharField(max_length=15, default='9876543210')  # N° Teléfono Paciente
    fecha_nacimiento_paciente = models.DateField(default='2000-01-01')  # Fecha de Nacimiento Paciente
    direccion_paciente = models.CharField(max_length=100, blank=True, default='')  # Dirección Paciente (Opcional)
    genero_paciente = models.CharField(max_length=20, default='No especificado')  # Género Paciente

    def __str__(self):
        return f"{self.nombres_paciente} {self.primer_apellido_paciente}"

class Informe(models.Model):
    id_informe = models.AutoField(primary_key=True)  # ID Informe
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE)  # ID Doctor
    paciente = models.ForeignKey(Paciente, on_delete=models.CASCADE)  # ID Paciente
    titulo_informe = models.CharField(max_length=200, default='Título por Defecto')  # Título del Informe
    descripcion_informe = models.TextField(default='Descripción por defecto.')  # Descripción del Informe
    notas_doctor = models.TextField(blank=True, default='')  # Notas o comentarios del doctor
    instrucciones_tratamiento = models.TextField(blank=True, default='')  # Instrucciones (medicamentos o tratamientos)
    fecha_informe = models.DateTimeField(auto_now_add=True)  # Fecha del Informe (subido)
    documentos_extra = models.FileField(upload_to='documentos_extra/', blank=True)  # Documentos extras

    def __str__(self):
        return f"Informe: {self.titulo_informe} - Paciente: {self.paciente}"

class Clinica(models.Model):
    id_clinica = models.AutoField(primary_key=True)  # ID Clínica
    nombre_clinica = models.CharField(max_length=100, default='Clinica Ejemplo')  # Nombre Clínica
    correo_clinica = models.EmailField(max_length=100, default='clinica@ejemplo.com')  # Correo Clínica
    telefono_clinica = models.CharField(max_length=15, default='5551234567')  # N° Teléfono Clínica

    def __str__(self):
        return self.nombre_clinica

class SedeClinica(models.Model):
    id_sede = models.AutoField(primary_key=True)  # ID Sede
    clinica = models.ForeignKey(Clinica, on_delete=models.CASCADE)  # ID Clínica
    region_sede = models.CharField(max_length=30, default='Región Ejemplo')  # Región Sede
    comuna_sede = models.CharField(max_length=30, default='Comuna Ejemplo')  # Comuna Sede
    direccion_sede = models.CharField(max_length=100, default='Dirección Ejemplo')  # Dirección Sede
    telefono_sede = models.CharField(max_length=15, default='1234567890')  # Teléfono Sede

    def __str__(self):
        return f"Sede de {self.clinica} en {self.comuna_sede}, {self.region_sede}"

class DoctorClinica(models.Model):
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE)  # ID Doctor
    clinica = models.ForeignKey(Clinica, on_delete=models.CASCADE)  # ID Clínica

    class Meta:
        unique_together = (('doctor', 'clinica'),)

    def __str__(self):
        return f"{self.doctor} - {self.clinica}"

class PacienteInforme(models.Model):
    id_paciente_informe = models.AutoField(primary_key=True)  # ID autoincrementable
    paciente = models.ForeignKey(Paciente, on_delete=models.CASCADE)  # ID Paciente
    informe = models.ForeignKey(Informe, on_delete=models.CASCADE)  # ID Informe
    fecha = models.DateField(auto_now_add=True)  # Fecha

    def __str__(self):
        return f"Informe de {self.paciente} - ID: {self.informe.id_informe}"

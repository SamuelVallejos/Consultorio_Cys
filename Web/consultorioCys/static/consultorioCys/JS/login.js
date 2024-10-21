
// Obtener los botones y formularios
const btnPaciente = document.getElementById('btnPaciente');
const btnDoctor = document.getElementById('btnDoctor');
const pacienteForm = document.getElementById('pacienteForm');
const doctorForm = document.getElementById('doctorForm');

// Función para mostrar el formulario del paciente y ocultar el del doctor
btnPaciente.addEventListener('click', () => {
  pacienteForm.style.display = 'block';
  doctorForm.style.display = 'none';
});

// Función para mostrar el formulario del doctor y ocultar el del paciente
btnDoctor.addEventListener('click', () => {
  doctorForm.style.display = 'block';
  pacienteForm.style.display = 'none';
});

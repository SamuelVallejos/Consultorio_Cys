function showForm(role) {
    const formPaciente = document.getElementById('formPaciente');
    const formDoctor = document.getElementById('formDoctor');
    const loginForm = document.getElementById('loginForm');
    const backButton = document.getElementById('backButton');
    const btnPaciente = document.getElementById('btnPaciente');
    const btnDoctor = document.getElementById('btnDoctor');
  
    if (role === 'paciente') {
      formPaciente.style.display = 'block';
      formDoctor.style.display = 'none';
      btnDoctor.style.display = 'none';
    } else {
      formDoctor.style.display = 'block';
      formPaciente.style.display = 'none';
      btnPaciente.style.display = 'none';
    }
  
    loginForm.style.display = 'block';
    backButton.style.display = 'block';
  }
  
  function resetSelection() {
    const formPaciente = document.getElementById('formPaciente');
    const formDoctor = document.getElementById('formDoctor');
    const loginForm = document.getElementById('loginForm');
    const backButton = document.getElementById('backButton');
    const btnPaciente = document.getElementById('btnPaciente');
    const btnDoctor = document.getElementById('btnDoctor');
  
    formPaciente.style.display = 'none';
    formDoctor.style.display = 'none';
    loginForm.style.display = 'none';
    backButton.style.display = 'none';
  
    btnPaciente.style.display = 'inline-block';
    btnDoctor.style.display = 'inline-block';
  }
  
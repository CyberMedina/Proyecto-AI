// Esperar a que el DOM esté completamente cargado
document.addEventListener("DOMContentLoaded", function () {
  
  // Obtener el formulario y los elementos de entrada
  const form = document.querySelector(".sign-in-form");
  const emailInput = document.querySelector("#email");
  const passwordInput = form.querySelector("#password");
  const confirmPasswordInput = form.querySelector("#confirm-password");
  const signBtn = form.querySelector(".sign-btn");
  // Obtén referencia al botón de saltar validaciones
  const skipValidationBtn = document.querySelector(".skip-validation-btn");
  

  // Elementos para el correcto cambio de formulario
  const toggle_btn = document.querySelectorAll(".toggle");
  const bullets = document.querySelectorAll(".bullets span");
  const main = document.querySelector("main");
  const images = document.querySelectorAll(".image");

  // Elementos para mostrar mensajes de error
  const errorEmailTooltip = form.querySelector("#error-email-tooltip");
  const passwordErrorTooltip = form.querySelector("#password-error");
  const confirmPasswordErrorTooltip = form.querySelector("#confirm-password-error");

  // Agrega un oyente de evento al botón para saltar validaciones
  skipValidationBtn.addEventListener("click", function () {
    // Cambia a la otra vista directamente
    main.classList.toggle("sign-up-mode");

    // Habilita el botón de envío ya que hemos saltado las validaciones
    signBtn.disabled = false;

    // Puedes ocultar los mensajes de error aquí si lo deseas
    hideTooltip(errorEmailTooltip);
    hideTooltip(passwordErrorTooltip);
    hideTooltip(confirmPasswordErrorTooltip);
  });

  // Función para verificar si todos los campos de entrada están llenos
  function checkAllInputsFilled() {
    const inputs = form.querySelectorAll("input[required]");
    return Array.from(inputs).every((input) => input.value.trim() !== "");
  }

  // Función para mostrar el tooltip
  function showTooltip(tooltip) {
    tooltip.style.display = "block";
  }

  // Función para ocultar el tooltip
  function hideTooltip(tooltip) {
    tooltip.style.display = "none";
  }

  // Función para verificar el formato de correo electrónico
  function isValidEmail(email) {
    const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailPattern.test(email);
  }

  // Función para verificar la longitud de la contraseña
  function isValidPassword(password) {
    return password.length >= 8 && password.length <= 16;
  }

  // Función para manejar el evento de entrada para el correo electrónico
  emailInput.addEventListener("input", function () {
    const email = this.value.trim();
    if (email !== "" && !isValidEmail(email)) {
      showTooltip(errorEmailTooltip);
      errorEmailTooltip.textContent = "Debe proporcionar un correo electrónico válido";
    } else {
      hideTooltip(errorEmailTooltip);
    }
    enableOrDisableSubmitButton();
  });

  // Función para manejar el evento de entrada para la contraseña
  passwordInput.addEventListener("input", function () {
    const password = this.value.trim();
    if (password !== "" && !isValidPassword(password)) {
      showTooltip(passwordErrorTooltip);
      passwordErrorTooltip.textContent =
        "Debe introducir una contraseña con una cantidad mínima de 8 dígitos y una máxima de 16 dígitos";
      confirmPasswordInput.disabled = true;
      confirmPasswordInput.value = "";
      hideTooltip(confirmPasswordErrorTooltip);
    } else {
      hideTooltip(passwordErrorTooltip);
      confirmPasswordInput.disabled = false;
    }
    enableOrDisableSubmitButton();
  });

  // Función para manejar el evento de entrada para confirmar la contraseña
  confirmPasswordInput.addEventListener("input", function () {
    const password = passwordInput.value.trim();
    const confirmPassword = this.value.trim();
    if (confirmPassword !== password) {
      showTooltip(confirmPasswordErrorTooltip);
      confirmPasswordErrorTooltip.textContent = "Las contraseñas no coinciden";
    } else {
      hideTooltip(confirmPasswordErrorTooltip);
    }
    enableOrDisableSubmitButton();
  });

  // Función para habilitar o deshabilitar el botón de envío según los valores de entrada
  function enableOrDisableSubmitButton() {
    const isEmailValid = isValidEmail(emailInput.value.trim());
    const isPasswordValid = isValidPassword(passwordInput.value.trim());
    const isConfirmPasswordValid = confirmPasswordInput.value.trim() === passwordInput.value.trim();

    if (checkAllInputsFilled() && isEmailValid && isPasswordValid && isConfirmPasswordValid) {
      signBtn.disabled = false;
    } else {
      signBtn.disabled = true;
    }
  }

  toggle_btn.forEach((btn) => {
    btn.addEventListener("click", () => {
      main.classList.toggle("sign-up-mode");
    });
  });

  function moveSlider() {
    let register_user = this.dataset.value;

    let currentImage = document.querySelector(`.img-${register_user}`);
    images.forEach((img) => img.classList.remove("show"));
    currentImage.classList.add("show");

    const textSlider = document.querySelector(".text-group");
    textSlider.style.transform = `translateY(${-(register_user - 1) * 2.2}rem)`;

    bullets.forEach((bull) => bull.classList.remove("active"));
    this.classList.add("active");
  }

  // Al hacer clic al botón de siguiente este hace la función de moveslider y simula que ha sido tocado un bullet
  signBtn.addEventListener("click", () => {
    moveSlider.call(bullets[1]);
  });

  // Estado inicial del formulario
  confirmPasswordInput.disabled = true;
  signBtn.disabled = true;

  // Función para hacer que el textarea se autocreciente
  function autoGrowTextArea(textarea) {
    textarea.style.height = "auto";
    textarea.style.height = `${textarea.scrollHeight}px`;

    // Actualizar el label con la cantidad de caracteres escritos y el límite (100)
    const charCountLabel = document.getElementById("char-count-indicaciones");
    const currentCount = textarea.value.length;
    charCountLabel.textContent = `${currentCount}/100`;

    // Limitar la escritura cuando se alcanzan los 100 caracteres
    if (currentCount >= 100) {
      textarea.value = textarea.value.slice(0, 100);
      charCountLabel.style.color = "red"; // Cambiar el color del label si se alcanza el límite
    } else {
      charCountLabel.style.color = "#bbb"; // Restaurar el color del label si no se alcanza el límite
    }
  }

  // Función para limitar el número de dígitos en el campo de teléfono a 8
  function limitInputToEightDigits(event) {
    const input = event.target;
    const inputValue = input.value.replace(/\D/g, ''); // Elimina todos los caracteres no numéricos
    const maxLength = 8;

    if (inputValue.length > maxLength) {
      // Trunca el valor a 8 dígitos si es más largo
      input.value = inputValue.slice(0, maxLength);
    } else {
      input.value = inputValue; // Si tiene menos de 8 dígitos, simplemente asigna el valor sin cambios
    }
  }

  // Evento de entrada para el textarea para ajustar su tamaño automáticamente
  const textArea = document.getElementById("text");
  if (textArea) {
    textArea.addEventListener("input", function () {
      autoGrowTextArea(this);
    });
  }

  // Evento de entrada para el campo de teléfono para limitar a 8 dígitos
  const phoneInput = document.querySelector("input[type='tel']");
  if (phoneInput) {
    phoneInput.addEventListener("input", function (event) {
      limitInputToEightDigits(event);
    });
  }

});

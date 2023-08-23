document.addEventListener("DOMContentLoaded", function () {
    // Obtener el formulario y el tooltip del correo electrónico
    const form = document.querySelector(".formlostpass");
    const emailInput = form.querySelector("#email");
    const errorEmailTooltip = form.querySelector("#error-email-tooltip");

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

    // Función para manejar el evento de entrada para el correo electrónico
    emailInput.addEventListener("input", function () {
        const email = this.value.trim();
        if (email !== "" && !isValidEmail(email)) {
            showTooltip(errorEmailTooltip);
            errorEmailTooltip.textContent = "Debe proporcionar un correo electrónico válido";
        } else {
            hideTooltip(errorEmailTooltip);
        }
    });


});

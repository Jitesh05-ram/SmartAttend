function togglePassword(passwordId, iconId) {

    const passwordInput = document.getElementById(passwordId);
    const eyeIcon = document.getElementById(iconId);

    if (!passwordInput || !eyeIcon) {
        return;
    }

    if (passwordInput.type === "password") {

        passwordInput.type = "text";

        eyeIcon.classList.remove("fa-eye");
        eyeIcon.classList.add("fa-eye-slash");

    } else {

        passwordInput.type = "password";

        eyeIcon.classList.remove("fa-eye-slash");
        eyeIcon.classList.add("fa-eye");
    }
}
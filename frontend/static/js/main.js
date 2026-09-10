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


/* ================================================================
   STUDENT BULK SELECT / DELETE
   Used on the Students page. Each row checkbox has the class
   "student-select-checkbox"; the "select all" checkbox has the id
   "selectAllStudents"; the bulk delete button has the id
   "bulkDeleteBtn" and a data-count-label element with id
   "bulkDeleteCount".
================================================================ */

function getStudentCheckboxes() {
    return Array.from(document.querySelectorAll(".student-select-checkbox"));
}

function updateBulkDeleteState() {

    const checkboxes = getStudentCheckboxes();
    const checkedCount = checkboxes.filter((cb) => cb.checked).length;

    const bulkBtn = document.getElementById("bulkDeleteBtn");
    const countLabel = document.getElementById("bulkDeleteCount");
    const selectAll = document.getElementById("selectAllStudents");

    if (bulkBtn) {
        bulkBtn.disabled = checkedCount === 0;
    }

    if (countLabel) {
        countLabel.textContent = checkedCount > 0 ? " (" + checkedCount + ")" : "";
    }

    if (selectAll) {
        selectAll.checked = checkboxes.length > 0 && checkedCount === checkboxes.length;
        selectAll.indeterminate = checkedCount > 0 && checkedCount < checkboxes.length;
    }
}

function toggleSelectAllStudents(selectAllCheckbox) {
    getStudentCheckboxes().forEach((cb) => {
        cb.checked = selectAllCheckbox.checked;
    });
    updateBulkDeleteState();
}

function confirmBulkDeleteStudents() {

    const checkedCount = getStudentCheckboxes().filter((cb) => cb.checked).length;

    if (checkedCount === 0) {
        return false;
    }

    const plural = checkedCount === 1 ? "student" : "students";

    return confirm(
        "Delete " + checkedCount + " selected " + plural + "? " +
        "This will also remove their attendance records. This cannot be undone."
    );
}

document.addEventListener("DOMContentLoaded", function () {
    getStudentCheckboxes().forEach((cb) => {
        cb.addEventListener("change", updateBulkDeleteState);
    });
    updateBulkDeleteState();
});
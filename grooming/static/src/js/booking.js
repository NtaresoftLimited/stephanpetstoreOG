/** @odoo-module **/

document.addEventListener("DOMContentLoaded", () => {
    document.querySelectorAll(".grooming-package-select").forEach((link) => {
        link.addEventListener("click", () => {
            const select = document.getElementById("grooming-service");
            if (select) select.value = link.dataset.serviceId || "";
        });
    });
    const form = document.getElementById("grooming-booking-form");
    if (form) {
        form.addEventListener("submit", () => {
            const button = form.querySelector("button[type='submit']");
            if (button) {
                button.disabled = true;
                button.textContent = "Recording booking...";
            }
        });
    }
});

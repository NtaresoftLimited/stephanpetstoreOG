/** @odoo-module **/

const initializeStephanHeader = () => {
    document.querySelectorAll("[data-stephans-header='true']").forEach((header) => {
        if (header.dataset.initialized === "true") return;
        const button = header.querySelector("[data-stephans-menu-button='true']");
        const menu = header.querySelector("[data-stephans-menu='true']");
        if (!button || !menu) return;
        button.addEventListener("click", () => {
            const open = menu.classList.toggle("is-open");
            button.setAttribute("aria-expanded", String(open));
        });
        header.dataset.initialized = "true";
    });
};

document.addEventListener("DOMContentLoaded", initializeStephanHeader);
document.addEventListener("website_preview_ready", initializeStephanHeader);


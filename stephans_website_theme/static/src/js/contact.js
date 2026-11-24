(function () {
    "use strict";

    function initialiseContactModal() {
        const modal = document.querySelector("[data-contact-modal]");
        const openButton = document.querySelector("[data-contact-open]");
        if (!modal || !openButton) return;

        const closeButton = modal.querySelector("[data-contact-close]");
        const firstField = modal.querySelector("input:not([type='hidden'])");
        const open = () => {
            modal.classList.add("is-open");
            modal.setAttribute("aria-hidden", "false");
            document.body.classList.add("sp-contact-modal-open");
            window.setTimeout(() => firstField && firstField.focus(), 30);
        };
        const close = () => {
            modal.classList.remove("is-open");
            modal.setAttribute("aria-hidden", "true");
            document.body.classList.remove("sp-contact-modal-open");
            openButton.focus();
        };

        openButton.addEventListener("click", open);
        closeButton && closeButton.addEventListener("click", close);
        modal.addEventListener("click", (event) => {
            if (event.target === modal) close();
        });
        document.addEventListener("keydown", (event) => {
            if (event.key === "Escape" && modal.classList.contains("is-open")) close();
        });
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", initialiseContactModal, { once: true });
    } else {
        initialiseContactModal();
    }
})();

/** @odoo-module **/

const initializeStephanHeader = () => {
    document.querySelectorAll("[data-stephans-header='true']").forEach((header) => {
        if (header.dataset.initialized === "true") return;

        const mobileButtons = header.querySelectorAll("[data-stephans-menu-button='true']");
        const mobileMenu = header.querySelector("[data-stephans-menu='true']");
        const megaItems = [...header.querySelectorAll("[data-stephans-mega='true']")];
        let closeTimer;

        const closeMegas = (except = null) => {
            megaItems.forEach((item) => {
                if (item === except) return;
                item.classList.remove("is-open");
                item.querySelector(":scope > button")?.setAttribute("aria-expanded", "false");
            });
        };

        const setMobileOpen = (open) => {
            header.classList.toggle("is-mobile-open", open);
            mobileMenu?.classList.toggle("is-open", open);
            mobileButtons.forEach((button) => button.setAttribute("aria-expanded", String(open)));
            if (!open) closeMegas();
        };

        mobileButtons.forEach((button) => {
            button.addEventListener("click", () => setMobileOpen(!header.classList.contains("is-mobile-open")));
        });

        megaItems.forEach((item) => {
            const button = item.querySelector(":scope > button");
            const open = () => {
                window.clearTimeout(closeTimer);
                closeMegas(item);
                item.classList.add("is-open");
                button?.setAttribute("aria-expanded", "true");
            };
            const scheduleClose = () => {
                closeTimer = window.setTimeout(() => closeMegas(), 180);
            };

            item.addEventListener("mouseenter", open);
            item.addEventListener("mouseleave", scheduleClose);
            button?.addEventListener("click", (event) => {
                event.stopPropagation();
                item.classList.contains("is-open") ? closeMegas() : open();
            });
        });

        const updateScrollState = () => header.classList.toggle("is-scrolled", window.scrollY > 72);
        window.addEventListener("scroll", updateScrollState, { passive: true });
        updateScrollState();

        document.addEventListener("click", (event) => {
            if (!header.contains(event.target)) {
                closeMegas();
                setMobileOpen(false);
            }
        });
        document.addEventListener("keydown", (event) => {
            if (event.key === "Escape") {
                closeMegas();
                setMobileOpen(false);
            }
        });
        header.dataset.initialized = "true";
    });
};

document.addEventListener("DOMContentLoaded", initializeStephanHeader);
document.addEventListener("website_preview_ready", initializeStephanHeader);

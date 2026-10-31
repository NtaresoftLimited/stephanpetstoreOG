/** @odoo-module **/

const initializeStephanHeader = () => {
    document.querySelectorAll("[data-stephans-header='true']").forEach((header) => {
        if (header.dataset.initialized === "true") return;

        const mobileButtons = header.querySelectorAll("[data-stephans-menu-button='true']");
        const mobileMenu = header.querySelector("[data-stephans-menu='true']");
        const megaItems = [...header.querySelectorAll("[data-stephans-mega='true']")];
        let closeTimer;
        let pinnedItem = null;

        const closeMegas = (except = null) => {
            megaItems.forEach((item) => {
                if (item === except) return;
                item.classList.remove("is-open");
                item.querySelector(":scope > button")?.setAttribute("aria-expanded", "false");
            });
        };

        const resetMega = (item) => {
            const mega = item.querySelector(":scope > .stephans-mega");
            mega?.classList.remove("is-expanded");
            mega?.querySelectorAll(".stephans-mega__group.is-items-open").forEach((group) => group.classList.remove("is-items-open"));
            const expandButton = mega?.querySelector("[data-mega-expand]");
            if (expandButton) expandButton.firstElementChild.textContent = expandButton.dataset.labelAll;
            mega?.querySelectorAll("[data-group-toggle]").forEach((button) => {
                button.setAttribute("aria-expanded", "false");
                button.firstElementChild.textContent = "View all";
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
                if (pinnedItem === item) return;
                closeTimer = window.setTimeout(() => closeMegas(), 180);
            };

            item.addEventListener("mouseenter", open);
            item.addEventListener("mouseleave", scheduleClose);
            button?.addEventListener("click", (event) => {
                event.stopPropagation();
                if (pinnedItem === item) {
                    pinnedItem = null;
                    closeMegas();
                } else {
                    pinnedItem = item;
                    open();
                }
            });

            item.querySelectorAll("[data-group-toggle]").forEach((toggle) => {
                toggle.addEventListener("click", (event) => {
                    event.stopPropagation();
                    const group = toggle.closest(".stephans-mega__group");
                    const expanded = group.classList.toggle("is-items-open");
                    toggle.setAttribute("aria-expanded", String(expanded));
                    toggle.firstElementChild.textContent = expanded ? "Show less" : "View all";
                    const mega = item.querySelector(":scope > .stephans-mega");
                    mega?.classList.add("is-expanded");
                    const expandButton = mega?.querySelector("[data-mega-expand]");
                    if (expandButton) expandButton.firstElementChild.textContent = expandButton.dataset.labelFeatured;
                });
            });

            const expandButton = item.querySelector("[data-mega-expand]");
            expandButton?.addEventListener("click", (event) => {
                event.stopPropagation();
                const mega = item.querySelector(":scope > .stephans-mega");
                const expanded = mega.classList.toggle("is-expanded");
                expandButton.firstElementChild.textContent = expanded ? expandButton.dataset.labelFeatured : expandButton.dataset.labelAll;
            });

            item.addEventListener("focusin", open);
            item.addEventListener("focusout", (event) => {
                if (!item.contains(event.relatedTarget)) scheduleClose();
            });
        });

        let scrollFrame = 0;
        const updateScrollState = () => {
            scrollFrame = 0;
            header.classList.toggle("is-scrolled", window.scrollY > 72);
        };
        const requestScrollUpdate = () => {
            if (!scrollFrame) scrollFrame = window.requestAnimationFrame(updateScrollState);
        };
        window.addEventListener("scroll", requestScrollUpdate, { passive: true });
        updateScrollState();

        document.addEventListener("click", (event) => {
            if (!header.contains(event.target)) {
                megaItems.forEach(resetMega);
                pinnedItem = null;
                closeMegas();
                setMobileOpen(false);
            }
        });
        document.addEventListener("keydown", (event) => {
            if (event.key === "Escape") {
                megaItems.forEach(resetMega);
                pinnedItem = null;
                closeMegas();
                setMobileOpen(false);
            }
        });
        header.dataset.initialized = "true";
    });
};

document.addEventListener("DOMContentLoaded", initializeStephanHeader);
document.addEventListener("website_preview_ready", initializeStephanHeader);

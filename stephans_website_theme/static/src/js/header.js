/** @odoo-module **/

const initializeStephanHeader = () => {
    document.querySelectorAll("[data-stephans-header='true']").forEach((header) => {
        if (header.dataset.initialized === "true") return;

        const mobileButtons = header.querySelectorAll("[data-stephans-menu-button='true']");
        const mobileMenu = header.querySelector("[data-stephans-menu='true']");
        const megaItems = [...header.querySelectorAll("[data-stephans-mega='true']")];
        let closeTimer;
        let pinnedItem = null;
        let openItem = null;

        const isDesktop = () => window.matchMedia("(min-width: 992px)").matches;

        const cancelClose = () => {
            window.clearTimeout(closeTimer);
            closeTimer = null;
        };

        const closeMegas = (except = null) => {
            megaItems.forEach((item) => {
                if (item === except) return;
                item.classList.remove("is-open");
                item.querySelector(":scope > button")?.setAttribute("aria-expanded", "false");
            });
            if (!except) {
                header.classList.remove("is-mega-open");
                openItem = null;
            } else {
                openItem = except;
            }
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
                cancelClose();
                closeMegas(item);
                item.classList.add("is-open");
                header.classList.add("is-mega-open");
                button?.setAttribute("aria-expanded", "true");
                openItem = item;
            };
            const scheduleClose = () => {
                cancelClose();
                if (pinnedItem && openItem === pinnedItem) return;
                closeTimer = window.setTimeout(() => closeMegas(), 180);
            };

            item.addEventListener("pointerenter", (event) => {
                if (!isDesktop() || event.pointerType === "touch") return;
                open();
            });
            item.addEventListener("mouseleave", scheduleClose);
            button?.addEventListener("click", (event) => {
                event.stopPropagation();
                if (item.classList.contains("is-open") && pinnedItem === item) {
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
            header.classList.toggle("is-scrolled", window.scrollY > 10);
        };
        const requestScrollUpdate = () => {
            if (!scrollFrame) scrollFrame = window.requestAnimationFrame(updateScrollState);
        };
        window.addEventListener("scroll", requestScrollUpdate, { passive: true });
        updateScrollState();

        const backdrop = header.querySelector("[data-stephans-backdrop='true']");
        backdrop?.addEventListener("click", () => {
            megaItems.forEach(resetMega);
            pinnedItem = null;
            closeMegas();
            setMobileOpen(false);
        });

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
        window.addEventListener("resize", () => {
            if (!isDesktop()) {
                pinnedItem = null;
                closeMegas();
            }
        }, { passive: true });
        header.dataset.initialized = "true";
    });
};

// Auto-rotate four-card live-catalog sets every 20 seconds.
const initializeProductRotator = () => {
    document.querySelectorAll("[data-stephans-product-rotator='true']").forEach((rotator) => {
        if (rotator.dataset.initialized === "true") return;

        const slides = Array.from(rotator.querySelectorAll(".stephans-products-slide"));
        const dots = Array.from(rotator.querySelectorAll(".stephans-rotator-dot"));
        if (slides.length <= 1) return;

        const ROTATION_MS = 20000;
        let currentIndex = Math.max(0, slides.findIndex((slide) => slide.classList.contains("is-active")));
        let isPointerPaused = false;
        let isFocusPaused = false;
        let timer = null;

        const preloadSlide = (index) => {
            slides[index]?.querySelectorAll("img[loading='lazy']").forEach((image) => {
                const preload = new Image();
                preload.src = image.currentSrc || image.src;
            });
        };

        const showSlide = (nextIndex) => {
            const normalizedIndex = (nextIndex + slides.length) % slides.length;
            slides.forEach((slide, index) => {
                const active = index === normalizedIndex;
                slide.classList.toggle("is-active", active);
                slide.setAttribute("aria-hidden", String(!active));
                slide.inert = !active;
                if (dots[index]) {
                    dots[index].classList.toggle("is-active", active);
                    dots[index].setAttribute("aria-current", String(active));
                }
            });
            currentIndex = normalizedIndex;
            preloadSlide((currentIndex + 1) % slides.length);
        };

        const isPaused = () => isPointerPaused || isFocusPaused || document.hidden;

        const scheduleNext = () => {
            window.clearTimeout(timer);
            timer = window.setTimeout(() => {
                if (!isPaused()) showSlide(currentIndex + 1);
                scheduleNext();
            }, ROTATION_MS);
        };

        rotator.addEventListener("pointerenter", () => { isPointerPaused = true; });
        rotator.addEventListener("pointerleave", () => { isPointerPaused = false; scheduleNext(); });
        rotator.addEventListener("focusin", () => { isFocusPaused = true; });
        rotator.addEventListener("focusout", (event) => {
            if (!rotator.contains(event.relatedTarget)) {
                isFocusPaused = false;
                scheduleNext();
            }
        });
        document.addEventListener("visibilitychange", () => {
            if (!document.hidden) scheduleNext();
        });

        dots.forEach((dot, idx) => {
            dot.addEventListener("click", () => {
                showSlide(idx);
                scheduleNext();
            });
        });

        showSlide(currentIndex);
        scheduleNext();
        rotator.dataset.initialized = "true";
    });
};

const initializeStephanWebsite = () => {
    initializeStephanHeader();
    initializeProductRotator();
};

if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initializeStephanWebsite, { once: true });
} else {
    initializeStephanWebsite();
}
document.addEventListener("website_preview_ready", initializeStephanWebsite);
window.addEventListener("pageshow", initializeStephanWebsite);

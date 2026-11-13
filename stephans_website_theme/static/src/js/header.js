/** @odoo-module **/

const initializeStephanHeader = () => {
    document.querySelectorAll("[data-stephans-header='true']").forEach((header) => {
        if (header.dataset.initialized === "true") return;

        const mobileButtons = header.querySelectorAll("[data-stephans-menu-button='true']");
        const closeButtons = header.querySelectorAll("[data-stephans-menu-close='true']");
        const mobileMenu = header.querySelector("[data-stephans-menu='true']");
        const megaItems = [...header.querySelectorAll("[data-stephans-mega='true']")];
        const backdrop = header.querySelector("[data-stephans-backdrop='true']");
        let closeTimer = null;
        // Mirrors pinnedCategoryRef in SecondaryStickyHeader.tsx: once a
        // category is clicked, hover-out never closes the menu; only an
        // outside pointer, Escape, the backdrop or navigation does.
        let pinnedItem = null;

        const isDesktop = () => window.matchMedia("(min-width: 992px)").matches;
        const megaOf = (item) => item.querySelector(":scope > .stephans-mega");
        const buttonOf = (item) => item.querySelector(":scope > button");

        const cancelClose = () => {
            window.clearTimeout(closeTimer);
            closeTimer = null;
        };

        const closeMegas = (except = null) => {
            megaItems.forEach((item) => {
                if (item === except) return;
                item.classList.remove("is-open");
                buttonOf(item)?.setAttribute("aria-expanded", "false");
            });
            header.classList.toggle("is-mega-open", Boolean(except) && isDesktop());
        };

        const openMega = (item) => {
            cancelClose();
            closeMegas(item);
            item.classList.add("is-open");
            buttonOf(item)?.setAttribute("aria-expanded", "true");
            header.classList.toggle("is-mega-open", isDesktop());
        };

        const scheduleClose = () => {
            cancelClose();
            if (pinnedItem) return;
            closeTimer = window.setTimeout(() => closeMegas(), 180);
        };

        const resetMega = (item) => {
            const mega = megaOf(item);
            if (!mega) return;
            mega.classList.remove("is-expanded");
            mega.querySelectorAll(".stephans-mega__group.is-items-open").forEach((group) => group.classList.remove("is-items-open"));
            const expandButton = mega.querySelector("[data-mega-expand]");
            if (expandButton) expandButton.firstElementChild.textContent = expandButton.dataset.labelAll;
            mega.querySelectorAll("[data-group-toggle]").forEach((button) => {
                button.setAttribute("aria-expanded", "false");
                button.firstElementChild.textContent = "View all";
            });
        };

        const closeAll = () => {
            cancelClose();
            pinnedItem = null;
            closeMegas();
        };

        const setMobileOpen = (open) => {
            header.classList.toggle("is-mobile-open", open);
            mobileMenu?.classList.toggle("is-open", open);
            document.documentElement.classList.toggle("stephans-drawer-open", open);
            mobileButtons.forEach((button) => button.setAttribute("aria-expanded", String(open)));
            if (!open) closeAll();
        };

        mobileButtons.forEach((button) => button.setAttribute("aria-controls", "stephans-nav-drawer"));

        // All header button clicks are handled here, in the CAPTURE phase on
        // the header. Odoo 20's web.assets_frontend_minimal binds its own
        // click listener on <button>s that swallows/queues clicks until the
        // lazy bundle loads, so per-button listeners never fire reliably.
        // Stopping propagation here also prevents Odoo from replaying the
        // click later (which would double-toggle the drawer accordions).
        header.addEventListener("click", (event) => {
            const target = event.target instanceof Element ? event.target : null;
            if (!target) return;

            const menuButton = target.closest("[data-stephans-menu-button='true']");
            if (menuButton) {
                event.stopPropagation();
                setMobileOpen(!header.classList.contains("is-mobile-open"));
                return;
            }
            if (target.closest("[data-stephans-menu-close='true']")) {
                event.stopPropagation();
                setMobileOpen(false);
                return;
            }
            if (backdrop && target === backdrop) {
                event.stopPropagation();
                megaItems.forEach(resetMega);
                closeAll();
                return;
            }

            const item = target.closest("[data-stephans-mega='true']");
            if (!item) return;
            const mega = megaOf(item);

            const toggle = target.closest("[data-group-toggle]");
            if (toggle) {
                event.stopPropagation();
                const group = toggle.closest(".stephans-mega__group");
                const expanded = group.classList.toggle("is-items-open");
                toggle.setAttribute("aria-expanded", String(expanded));
                toggle.firstElementChild.textContent = expanded ? "Show less" : "View all";
                // Expanding one group widens the whole panel, as in CategoryMegaMenu.tsx.
                mega?.classList.add("is-expanded");
                const expandButton = mega?.querySelector("[data-mega-expand]");
                if (expandButton) expandButton.firstElementChild.textContent = expandButton.dataset.labelFeatured;
                return;
            }

            const expandButton = target.closest("[data-mega-expand]");
            if (expandButton) {
                event.stopPropagation();
                const expanded = mega.classList.toggle("is-expanded");
                expandButton.firstElementChild.textContent = expanded ? expandButton.dataset.labelFeatured : expandButton.dataset.labelAll;
                return;
            }

            if (target.closest("a[href]")) {
                // Following a link closes the menu / drawer (onNavigate in React).
                closeAll();
                if (!isDesktop()) setMobileOpen(false);
                return;
            }

            if (target.closest(".stephans-mega-item > button") === buttonOf(item)) {
                event.stopPropagation();
                if (isDesktop()) {
                    // Desktop: click pins the panel open (Next.js behaviour).
                    pinnedItem = item;
                    openMega(item);
                } else if (item.classList.contains("is-open")) {
                    // Drawer: single-open accordion.
                    closeAll();
                } else {
                    openMega(item);
                }
            }
        }, true);

        megaItems.forEach((item) => {
            const button = buttonOf(item);

            item.addEventListener("pointerenter", (event) => {
                if (!isDesktop() || event.pointerType === "touch") return;
                openMega(item);
            });
            item.addEventListener("pointerleave", (event) => {
                if (!isDesktop() || event.pointerType === "touch") return;
                scheduleClose();
            });

            // Keyboard users: tabbing into a category opens it on desktop.
            button?.addEventListener("keyup", (event) => {
                if (isDesktop() && event.key === "Tab") openMega(item);
            });
            item.addEventListener("focusout", (event) => {
                if (isDesktop() && event.relatedTarget && !item.contains(event.relatedTarget)) scheduleClose();
            });
        });

        // Sliding pill indicator for the floating home nav (Header.tsx).
        const homeNav = header.querySelector(".stephans-homebar__nav");
        const indicator = homeNav?.querySelector(".stephans-homebar__indicator");
        if (homeNav && indicator) {
            const links = [...homeNav.querySelectorAll("a[href]")];
            const path = window.location.pathname.replace(/\/+$/, "") || "/";
            const activeLink = links.find((link) => {
                const href = link.getAttribute("href");
                return href === path || (href !== "/" && path.startsWith(href + "/"));
            }) || null;
            const moveIndicator = (link) => {
                links.forEach((candidate) => candidate.classList.toggle("is-indicated", candidate === link));
                if (!link) {
                    indicator.classList.remove("is-visible");
                    return;
                }
                indicator.style.left = link.offsetLeft + "px";
                indicator.style.width = link.offsetWidth + "px";
                indicator.classList.add("is-visible");
            };
            links.forEach((link) => {
                link.addEventListener("pointerenter", () => moveIndicator(link));
                link.addEventListener("focus", () => moveIndicator(link));
            });
            homeNav.addEventListener("pointerleave", () => moveIndicator(activeLink));
            homeNav.addEventListener("focusout", (event) => {
                if (!homeNav.contains(event.relatedTarget)) moveIndicator(activeLink);
            });
            window.addEventListener("resize", () => moveIndicator(activeLink), { passive: true });
            moveIndicator(activeLink);
        }

        // Scroll state: on the home page this swaps the floating bar for the
        // full sticky header (threshold matches Header.tsx: scrollY > 10).
        let scrollFrame = 0;
        const updateScrollState = () => {
            scrollFrame = 0;
            const scrolled = window.scrollY > 10;
            if (scrolled !== header.classList.contains("is-scrolled")) {
                header.classList.toggle("is-scrolled", scrolled);
                if (header.classList.contains("is-home") && isDesktop()) closeAll();
            }
        };
        const requestScrollUpdate = () => {
            if (!scrollFrame) scrollFrame = window.requestAnimationFrame(updateScrollState);
        };
        window.addEventListener("scroll", requestScrollUpdate, { passive: true });
        updateScrollState();

        document.addEventListener("pointerdown", (event) => {
            if (!header.contains(event.target)) {
                closeAll();
                setMobileOpen(false);
            }
        });
        document.addEventListener("keydown", (event) => {
            if (event.key === "Escape") {
                megaItems.forEach(resetMega);
                closeAll();
                setMobileOpen(false);
            }
        });

        let wasDesktop = isDesktop();
        window.addEventListener("resize", () => {
            const desktop = isDesktop();
            if (desktop !== wasDesktop) {
                wasDesktop = desktop;
                closeAll();
                setMobileOpen(false);
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
        // Pause for keyboard focus only. A mouse/touch click on a dot leaves
        // focus on the dot, which previously froze rotation for good.
        rotator.addEventListener("focusin", (event) => {
            if (event.target instanceof Element && event.target.matches(":focus-visible")) isFocusPaused = true;
        });
        rotator.addEventListener("focusout", (event) => {
            if (!rotator.contains(event.relatedTarget)) {
                isFocusPaused = false;
                scheduleNext();
            }
        });
        document.addEventListener("visibilitychange", () => {
            if (!document.hidden) scheduleNext();
        });

        // Capture-phase delegation, for the same Odoo 20 click-swallowing reason as the header.
        rotator.addEventListener("click", (event) => {
            const dot = event.target instanceof Element ? event.target.closest(".stephans-rotator-dot") : null;
            const idx = dot ? dots.indexOf(dot) : -1;
            if (idx < 0) return;
            event.stopPropagation();
            showSlide(idx);
            scheduleNext();
        }, true);

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

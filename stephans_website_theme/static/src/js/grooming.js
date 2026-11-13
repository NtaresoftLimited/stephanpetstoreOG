(function () {
    "use strict";

    const PRICES = {
        dog: {
            standard: { small: 60000, medium: 70000, large: 80000 },
            super_premium: { small: 80000, medium: 90000, large: 100000 },
        },
        cat: {
            standard: { kitten: 60000, adult: 70000, senior: 80000 },
            super_premium: { kitten: 80000, adult: 90000, senior: 100000 },
        },
        small_animal: {
            super_premium: { hamster: 100000, junior_rabbit: 100000, adult_rabbit: 150000, guinea_pig: 100000 },
        },
    };

    const BREED_SIZES = {
        dog: [
            ["small", "Small Breeds"], ["medium", "Medium Breeds"], ["large", "Large Breeds"],
        ],
        cat: [
            ["kitten", "Kitten - (2 - 12 Months)"], ["adult", "Adult Cat - (1+ Year)"], ["senior", "Senior Cat - (5+ Years)"],
        ],
        small_animal: [
            ["hamster", "Hamster"], ["junior_rabbit", "Junior Rabbit (0 - 6 months)"],
            ["adult_rabbit", "Adult Rabbit (6 months +)"], ["guinea_pig", "Guinea Pig"],
        ],
    };

    const SERVICES = {
        standard: ["Warm Deep Clean Bath", "Blow Dry", "Ear Care", "Full Coat Brush Out", "Sanitary Trim (Private Area & Belly)"],
        super_premium: ["Warm Deep Clean Bath", "Blow Dry", "Ear Care", "Nail Care", "Dental Care", "De-shedding", "Full Hair Cut or Styling", "Flea & Tick Treatment", "Paw Balm Treatment", "Finishing Touches"],
    };

    const $ = (selector, root) => (root || document).querySelector(selector);
    const $$ = (selector, root) => Array.from((root || document).querySelectorAll(selector));
    const money = (amount) => "TZS " + Number(amount || 0).toLocaleString("en-US");

    function initGrooming(root) {
        if (!root || root.dataset.groomingReady === "true") return;
        root.dataset.groomingReady = "true";

        let prices = PRICES;
        try {
            if (root.dataset.prices) prices = JSON.parse(root.dataset.prices);
        } catch (error) {
            console.warn("Could not read Odoo grooming prices; using safe defaults.", error);
        }
        const detanglingFee = Number(root.dataset.detanglingFee || 30000);

        const tabs = $$(".grooming-tab", root);
        const petType = $("#field-pet-type", root);
        const breed = $("#field-breed-size", root);
        const packageField = $("#field-package", root);
        const form = $("#grooming-form", root);
        const detangling = $("#field-detangling", root);
        const status = $("#grooming-form-status", root);
        const submitButton = $("#btn-submit", root);
        if (!tabs.length || !petType || !breed || !packageField) return;

        function updateDetails() {
            const pkg = packageField.value;
            const size = breed.value;
            const type = petType.value;
            const included = $("#included-box", root);
            const includedTitle = $("#included-title", root);
            const includedServices = $("#included-services", root);
            const total = $("#total-box", root);

            if (pkg && SERVICES[pkg]) {
                included.style.display = "block";
                includedTitle.textContent = "What's included in your " + (pkg === "standard" ? "Essential" : "Signature") + " Package";
                includedServices.innerHTML = SERVICES[pkg].map((service) =>
                    '<div class="grooming-service-item"><svg class="grooming-check-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="20 6 9 17 4 12"></polyline></svg><span>' + service + "</span></div>"
                ).join("");
            } else if (included) {
                included.style.display = "none";
            }

            const basePrice = prices[type] && prices[type][pkg] && prices[type][pkg][size];
            if (basePrice) {
                const detVal = root.querySelector('input[name="detangling_type"]:checked')?.value;
                const detFee = detVal === "intensive" ? 150000 : detVal === "moderate" ? 100000 : 0;
                const price = basePrice + detFee;
                const typeLabel = type === "dog" ? "Dog" : type === "cat" ? "Cat" : "Small Animal";
                const sizeEntry = (BREED_SIZES[type] || []).find((entry) => entry[0] === size);
                $("#total-summary", root).textContent = typeLabel + " • " + (sizeEntry ? sizeEntry[1] : size) + " • " + (pkg === "standard" ? "Essential" : "Signature") + " Package";
                $("#total-amount", root).textContent = money(price);
                total.style.display = "flex";
            } else if (total) {
                total.style.display = "none";
            }
        }

        function rebuildOptions(type) {
            breed.replaceChildren(new Option("Breed Size", "", true, true));
            breed.options[0].disabled = true;
            (BREED_SIZES[type] || []).forEach(([value, label]) => breed.add(new Option(label, value)));

            packageField.replaceChildren(new Option("Service Package", "", true, true));
            packageField.options[0].disabled = true;
            if (type !== "small_animal") packageField.add(new Option("Essential", "standard"));
            packageField.add(new Option("Signature", "super_premium"));
            updateDetails();
        }

        function activate(type) {
            if (!prices[type]) return;
            tabs.forEach((tab) => {
                const selected = tab.dataset.tab === type;
                tab.classList.toggle("active", selected);
                tab.setAttribute("aria-selected", String(selected));
                tab.tabIndex = selected ? 0 : -1;
            });

            const grid = $("#packages-grid", root);
            const essential = $("#card-essential", root);
            const signature = $("#card-signature", root);
            const smallAnimal = type === "small_animal";
            grid.classList.toggle("single-col", smallAnimal);
            essential.style.display = smallAnimal ? "none" : "flex";
            signature.style.display = "flex";
            const essentialPrices = Object.values(prices[type]?.standard || {});
            const signaturePrices = Object.values(prices[type]?.super_premium || {});
            $("#price-essential", root).textContent = money(essentialPrices.length ? Math.min(...essentialPrices) : 60000);
            $("#price-signature", root).textContent = money(signaturePrices.length ? Math.min(...signaturePrices) : (smallAnimal ? 100000 : 80000));

            if (petType.value !== type) petType.value = type;
            rebuildOptions(type);
        }

        tabs.forEach((tab, index) => {
            const select = () => activate(tab.dataset.tab);
            tab.addEventListener("click", select);
            tab.addEventListener("pointerenter", (event) => {
                if (event.pointerType === "mouse") select();
            });
            tab.addEventListener("focus", select);
            tab.addEventListener("keydown", (event) => {
                if (event.key !== "ArrowLeft" && event.key !== "ArrowRight") return;
                event.preventDefault();
                const direction = event.key === "ArrowRight" ? 1 : -1;
                tabs[(index + direction + tabs.length) % tabs.length].focus();
            });
        });

        petType.addEventListener("change", () => activate(petType.value));
        breed.addEventListener("change", updateDetails);
        packageField.addEventListener("change", updateDetails);
        detangling?.addEventListener("change", updateDetails);
        root.querySelectorAll('input[name="detangling_type"]').forEach((r) => r.addEventListener("change", updateDetails));

        $$(".grooming-pkg-card", root).forEach((card) => {
            card.tabIndex = 0;
            const choose = () => {
                packageField.value = card.dataset.package;
                updateDetails();
                form.scrollIntoView({ behavior: "smooth", block: "start" });
            };
            card.addEventListener("click", choose);
            card.addEventListener("keydown", (event) => {
                if (event.key === "Enter" || event.key === " ") { event.preventDefault(); choose(); }
            });
        });

        const date = $("#field-date", root);
        const timeField = $("#field-time", root);
        const refreshTimeAvailability = () => {
            if (!date.value) return;
            const selectedDate = new Date(date.value + "T00:00:00");
            const now = new Date();
            const cutoff = new Date(now.getTime() + 15 * 60 * 1000);
            const isToday = selectedDate.toDateString() === now.toDateString();
            Array.from(timeField.options).forEach((option) => {
                if (!option.value) return;
                const [hour, minute] = option.value.split(":").map(Number);
                const slot = new Date(selectedDate);
                slot.setHours(hour, minute, 0, 0);
                option.disabled = selectedDate < new Date(now.getFullYear(), now.getMonth(), now.getDate()) || (isToday && slot < cutoff);
            });
            if (timeField.selectedOptions[0]?.disabled) timeField.value = "";
        };
        date.addEventListener("change", () => {
            if (date.value && new Date(date.value + "T12:00:00").getDay() === 0) {
                window.alert("We are closed on Sundays. Please select another day for your pet's grooming.");
                date.value = "";
            }
            refreshTimeAvailability();
        });

        form.addEventListener("submit", async (event) => {
            event.preventDefault();
            if (!form.reportValidity()) return;

            status.classList.remove("is-visible");
            status.textContent = "";
            submitButton.disabled = true;
            submitButton.setAttribute("aria-busy", "true");
            const originalLabel = submitButton.querySelector("span").textContent;
            submitButton.querySelector("span").textContent = "Saving appointment...";

            const type = petType.value;
            const size = breed.value;
            const pkg = packageField.value;
            const sizeEntry = (BREED_SIZES[type] || []).find((entry) => entry[0] === size);
            const typeLabel = type === "dog" ? "Dog" : type === "cat" ? "Cat" : "Small Animal";

            try {
                const response = await fetch("/grooming/book", {
                    method: "POST",
                    body: new FormData(form),
                    headers: { "X-Requested-With": "XMLHttpRequest", "Accept": "application/json" },
                });
                const result = await response.json();
                if (!response.ok || !result.ok) throw new Error(result.error || "The booking could not be saved.");

                const notes = $("#field-notes", root).value.trim();
                const message = [
                    "🐾 *NEW GROOMING BOOKING REQUEST*",
                    "*Odoo Reference:* " + result.reference,
                    "", "*CUSTOMER*",
                    "Name: " + $("#field-customer-name", root).value,
                    "Phone: " + $("#field-customer-phone", root).value,
                    "", "*PET DETAILS*",
                    "Pet: " + $("#field-pet-name", root).value + " (" + typeLabel + ")",
                    "Size / Stage: " + (sizeEntry ? sizeEntry[1] : size),
                    "", "*SERVICE*",
                    "Package: " + (pkg === "standard" ? "Essential" : "Signature"),
                    (() => {
                        const detVal = root.querySelector('input[name="detangling_type"]:checked')?.value;
                        if (detVal === "intensive") return "Detangling: Intensive (+TZS 150,000)";
                        if (detVal === "moderate") return "Detangling: Moderate (+TZS 100,000)";
                        return "Detangling: No";
                    })(),
                    "Date: " + result.date_label,
                    "Time: " + result.time_label,
                    "Total: " + result.total_formatted,
                    notes ? "Notes: " + notes : "",
                ].filter(Boolean).join("\n");
                window.location.href = "https://wa.me/255769324445?text=" + encodeURIComponent(message);
            } catch (error) {
                status.textContent = error.message || "The booking could not be saved. Please try again.";
                status.classList.add("is-visible");
                status.scrollIntoView({ behavior: "smooth", block: "center" });
                submitButton.disabled = false;
                submitButton.removeAttribute("aria-busy");
                submitButton.querySelector("span").textContent = originalLabel;
            }
        });

        activate(petType.value || "dog");
    }

    function boot() {
        $$(".grooming-site").forEach(initGrooming);
    }
    if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", boot, { once: true });
    else boot();
    window.addEventListener("pageshow", boot);
})();

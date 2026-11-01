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

        const tabs = $$(".grooming-tab", root);
        const petType = $("#field-pet-type", root);
        const breed = $("#field-breed-size", root);
        const packageField = $("#field-package", root);
        const form = $("#grooming-form", root);
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

            const price = PRICES[type] && PRICES[type][pkg] && PRICES[type][pkg][size];
            if (price) {
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
            if (!PRICES[type]) return;
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
            $("#price-essential", root).textContent = money(60000);
            $("#price-signature", root).textContent = money(smallAnimal ? 100000 : 80000);

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
        date.addEventListener("change", () => {
            if (date.value && new Date(date.value + "T12:00:00").getDay() === 0) {
                window.alert("We are closed on Sundays. Please select another day for your pet's grooming.");
                date.value = "";
            }
        });

        form.addEventListener("submit", (event) => {
            event.preventDefault();
            const type = petType.value;
            const size = breed.value;
            const pkg = packageField.value;
            const price = PRICES[type] && PRICES[type][pkg] && PRICES[type][pkg][size] || 0;
            const sizeEntry = (BREED_SIZES[type] || []).find((entry) => entry[0] === size);
            const typeLabel = type === "dog" ? "Dog" : type === "cat" ? "Cat" : "Small Animal";
            const bookingRef = "GRM-" + Math.random().toString(36).slice(2, 8).toUpperCase();
            const message = [
                "Hi Stephan's Pet Store!", "I want to book a grooming appointment:", "", "*GROOMING APPOINTMENT BOOKING*",
                "*Booking Ref:* #" + bookingRef,
                "*Customer Name:* " + $("#field-customer-name", root).value,
                "*Phone Number:* " + $("#field-customer-phone", root).value, "",
                "*PET DETAILS*", "*Pet Name:* " + $("#field-pet-name", root).value + " (" + typeLabel + ")",
                "*Breed Size:* " + (sizeEntry ? sizeEntry[1] : size), "", "*SERVICE DETAILS*",
                "*Selected Package:* " + (pkg === "standard" ? "Essential" : "Signature") + " Package",
                "*Preferred Date:* " + date.value, "*Preferred Time:* " + $("#field-time", root).value, "",
                "*Total Amount:* " + money(price),
            ].join("\n");
            const target = "https://wa.me/255769324445?text=" + encodeURIComponent(message);
            fetch("/grooming/book", { method: "POST", body: new FormData(form) }).finally(() => { window.location.href = target; });
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

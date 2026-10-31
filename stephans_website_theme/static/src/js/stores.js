(function () {
    "use strict";

    const stores = [
        { name: "Masaki Branch (Main)", address: "11 Slipway Rd, Masaki, Dar es Salaam", position: [-6.7452, 39.2825] },
        { name: "Mikocheni Branch", address: "59 Mikocheni A, Dar es Salaam", position: [-6.7733, 39.2699] },
    ];

    function initializeStoreDetails() {
        document.querySelectorAll(".sp-store-details-toggle").forEach((button) => {
            button.addEventListener("click", () => {
                const details = button.nextElementSibling;
                const expanded = button.getAttribute("aria-expanded") === "true";
                button.setAttribute("aria-expanded", String(!expanded));
                button.querySelector("span").textContent = expanded ? "＋" : "−";
                details.hidden = expanded;
            });
        });
    }

    function initializeStoreMap(attempt) {
        const element = document.getElementById("sp-store-map");
        if (!element || element.dataset.initialized === "true") return;
        if (!window.L) {
            if (attempt < 40) window.setTimeout(() => initializeStoreMap(attempt + 1), 100);
            return;
        }

        element.dataset.initialized = "true";
        element.parentElement.classList.add("is-ready");
        const map = window.L.map(element, { scrollWheelZoom: false }).setView([-6.7592, 39.2762], 13);
        window.L.tileLayer("https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png", {
            attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
            maxZoom: 19,
        }).addTo(map);

        const markerImage = element.dataset.markerImage;
        const icon = window.L.divIcon({
            className: "sp-leaflet-marker",
            html: '<div><img src="' + markerImage + '" alt=""/></div><i></i>',
            iconSize: [36, 44], iconAnchor: [18, 44], popupAnchor: [0, -44],
        });
        stores.forEach((store) => {
            const directions = "https://www.google.com/maps/dir/?api=1&destination=" + store.position.join(",");
            window.L.marker(store.position, { icon }).addTo(map).bindPopup(
                '<div class="sp-map-popup"><strong>' + store.name + '</strong><p>' + store.address + '</p><a href="' + directions + '" target="_blank" rel="noopener">Directions →</a></div>'
            );
        });
        window.setTimeout(() => map.invalidateSize(), 150);
    }

    function initializeStoresPage() {
        initializeStoreDetails();
        initializeStoreMap(0);
    }
    if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", initializeStoresPage, { once: true });
    else initializeStoresPage();
})();

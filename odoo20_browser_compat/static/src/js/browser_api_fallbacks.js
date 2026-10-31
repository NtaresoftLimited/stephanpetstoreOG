(function () {
    "use strict";

    // Clipboard is unavailable on plain HTTP origins except localhost. Odoo's
    // interactive tour helper reads writeText while its module is loading.
    if (!window.navigator.clipboard) {
        Object.defineProperty(window.navigator, "clipboard", {
            configurable: true,
            value: {
                readText: () => Promise.resolve(""),
                writeText: () => Promise.resolve(),
            },
        });
    } else if (typeof window.navigator.clipboard.writeText !== "function") {
        window.navigator.clipboard.writeText = () => Promise.resolve();
    }

    // Some extensions expose a partial chrome.runtime object. Odoo's mail PTT
    // service must not fail when the extension messaging function is absent.
    if (window.chrome?.runtime && typeof window.chrome.runtime.sendMessage !== "function") {
        try {
            window.chrome.runtime.sendMessage = () => Promise.resolve("1.0.0.0");
            if (typeof window.chrome.runtime.sendMessage !== "function") {
                Object.defineProperty(window.chrome.runtime, "sendMessage", {
                    configurable: true,
                    value: () => Promise.resolve("1.0.0.0"),
                });
            }
        } catch {
            // A frozen extension object cannot be repaired, but must not stop
            // the remaining compatibility setup.
        }
    }
})();

/**
 * Guard Discuss' push-to-talk extension service against browser extensions that expose a partial,
 * frozen `window.chrome.runtime` (no `sendMessage`). Odoo calls
 * `window.chrome?.runtime?.sendMessage(...)` while the service starts; optional chaining does not
 * protect a missing function, so the TypeError aborts service start-up in the web client.
 * browser_api_fallbacks.js repairs the object when it can; when the object is frozen it cannot, so
 * here the service falls back to a "push-to-talk extension not installed" stub instead.
 */
import { markup, proxy } from "@odoo/owl";
import { _t } from "@web/core/l10n/translation";
import { patch } from "@web/core/utils/patch";
import { pttExtensionHookService } from "@mail/discuss/call/common/ptt_extension_service";

const EXT_URL = "https://chromewebstore.google.com/detail/discuss-push-to-talk/mdiacebcbkmjjlpclnbcgiepgifcnpmg";

function runtimeIsBroken() {
    const runtime = window.chrome?.runtime;
    return Boolean(runtime) && typeof runtime.sendMessage !== "function";
}

function disabledPttService() {
    return proxy({
        isEnabled: false,
        voiceActivated: false,
        notifyIsTalking() {},
        subscribe() {},
        unsubscribe() {
            this.voiceActivated = false;
        },
        downloadURL: EXT_URL,
        get downloadText() {
            return _t(
                "Push-to-Talk works only while this tab is in focus. To use it outside this tab, we recommend installing our %(anchor_start)sextension%(anchor_end)s.",
                {
                    anchor_start: markup`<a href="${EXT_URL}" target="_blank" class="text-reset text-decoration-underline">`,
                    anchor_end: markup`</a>`,
                }
            );
        },
    });
}

patch(pttExtensionHookService, {
    start() {
        if (runtimeIsBroken()) {
            return disabledPttService();
        }
        try {
            return super.start(...arguments);
        } catch (error) {
            if (error instanceof TypeError) {
                console.warn("Discuss push-to-talk extension unavailable:", error.message);
                return disabledPttService();
            }
            throw error;
        }
    },
});

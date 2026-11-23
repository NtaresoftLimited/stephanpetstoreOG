(function () {
    "use strict";

    var DISMISS_KEY = "stephans_paw_popup_dismissed_at";
    var DISMISS_TTL_MS = 7 * 24 * 60 * 60 * 1000; // 7 days

    var FLAG_SVGS = {
        TZ: '<svg width="22" height="15" viewBox="0 0 22 15" style="border-radius:2.5px;box-shadow:0 0 0 0.5px rgba(0,0,0,0.12)" xmlns="http://www.w3.org/2000/svg"><clipPath id="o_paw_tz"><rect width="22" height="15" rx="2"/></clipPath><g clip-path="url(#o_paw_tz)"><rect width="22" height="15" fill="#1EB53A"/><polygon points="22,0 22,15 0,15" fill="#00A3DD"/><line x1="0" y1="15" x2="22" y2="0" stroke="#FCD116" stroke-width="5.2"/><line x1="0" y1="15" x2="22" y2="0" stroke="#111111" stroke-width="3.2"/></g></svg>',
        KE: '<svg width="22" height="15" viewBox="0 0 22 15" style="border-radius:2.5px;box-shadow:0 0 0 0.5px rgba(0,0,0,0.12)" xmlns="http://www.w3.org/2000/svg"><rect width="22" height="4.5" y="0" fill="#111111"/><rect width="22" height="1" y="4.5" fill="#FFFFFF"/><rect width="22" height="4" y="5.5" fill="#BB0000"/><rect width="22" height="1" y="9.5" fill="#FFFFFF"/><rect width="22" height="4.5" y="10.5" fill="#006600"/><ellipse cx="11" cy="7.5" rx="2" ry="3.4" fill="#BB0000" stroke="#FFFFFF" stroke-width="0.6"/></svg>',
        UG: '<svg width="22" height="15" viewBox="0 0 22 15" style="border-radius:2.5px;box-shadow:0 0 0 0.5px rgba(0,0,0,0.12)" xmlns="http://www.w3.org/2000/svg"><rect width="22" height="2.5" y="0" fill="#111111"/><rect width="22" height="2.5" y="2.5" fill="#FCDC04"/><rect width="22" height="2.5" y="5" fill="#D90000"/><rect width="22" height="2.5" y="7.5" fill="#111111"/><rect width="22" height="2.5" y="10" fill="#FCDC04"/><rect width="22" height="2.5" y="12.5" fill="#D90000"/><circle cx="11" cy="7.5" r="2.2" fill="#FFFFFF"/></svg>',
        RW: '<svg width="22" height="15" viewBox="0 0 22 15" style="border-radius:2.5px;box-shadow:0 0 0 0.5px rgba(0,0,0,0.12)" xmlns="http://www.w3.org/2000/svg"><rect width="22" height="7.5" y="0" fill="#00A1DE"/><rect width="22" height="3.75" y="7.5" fill="#FAD201"/><rect width="22" height="3.75" y="11.25" fill="#20603D"/><circle cx="16.8" cy="3.6" r="1.4" fill="#E5BE01"/></svg>'
    };

    function jsonRpc(url, params) {
        return fetch(url, {
            method: "POST",
            credentials: "same-origin",
            headers: {
                "Content-Type": "application/json",
                "Accept": "application/json"
            },
            body: JSON.stringify({
                jsonrpc: "2.0",
                method: "call",
                params: params || {},
                id: Math.floor(Math.random() * 1e9)
            })
        }).then(function (resp) {
            return resp.json();
        }).then(function (payload) {
            if (payload && payload.error) {
                var msg = (payload.error.data && payload.error.data.message) || payload.error.message || "Request failed.";
                return { ok: false, error: msg };
            }
            return (payload && payload.result) || { ok: false, error: "Unexpected response." };
        });
    }

    function isDismissedRecently() {
        try {
            var ts = Number(window.localStorage.getItem(DISMISS_KEY) || 0);
            return ts > 0 && (Date.now() - ts) < DISMISS_TTL_MS;
        } catch (e) {
            return false;
        }
    }

    function markDismissed() {
        try {
            window.localStorage.setItem(DISMISS_KEY, String(Date.now()));
        } catch (e) {
            // ignore storage errors
        }
    }

    function shouldAutoShowOnPath(path) {
        if (!path) return false;
        var blocked = ["/web/login", "/web/signup", "/my", "/odoo", "/shop/payment", "/payment/"];
        for (var i = 0; i < blocked.length; i++) {
            if (path.indexOf(blocked[i]) === 0) return false;
        }
        return true;
    }

    function initPawPopup() {
        var overlay = document.getElementById("o_paw_popup_overlay");
        if (!overlay || overlay.dataset.pawReady === "1") return;
        overlay.dataset.pawReady = "1";

        var step1 = overlay.querySelector("#o_paw_step_1");
        var step2 = overlay.querySelector("#o_paw_step_2");
        var step3 = overlay.querySelector("#o_paw_step_3");

        var flagBtn = overlay.querySelector("#o_paw_flag_btn");
        var flagSvg = overlay.querySelector("#o_paw_flag_svg");
        var flagMenu = overlay.querySelector("#o_paw_flag_menu");
        var dialEl = overlay.querySelector("#o_paw_dial_code");
        var phoneInput = overlay.querySelector("#o_paw_phone_input");
        var optInInput = overlay.querySelector("#o_paw_optin");
        var sendBtn = overlay.querySelector("#o_paw_send_btn");

        var displayPhone = overlay.querySelector("#o_paw_display_phone");
        var otpInput = overlay.querySelector("#o_paw_otp_input");
        var verifyBtn = overlay.querySelector("#o_paw_verify_btn");
        var resendBtn = overlay.querySelector("#o_paw_resend_btn");
        var changeNumBtn = overlay.querySelector("#o_paw_change_num_btn");

        var errorBox = overlay.querySelector("#o_paw_error_box");
        var infoBox = overlay.querySelector("#o_paw_info_box");

        var balancePts = overlay.querySelector("#o_paw_balance_pts");
        var balanceVal = overlay.querySelector("#o_paw_balance_val");
        var balanceBar = overlay.querySelector("#o_paw_balance_bar");
        var balanceCaption = overlay.querySelector("#o_paw_balance_caption");
        var doneBtn = overlay.querySelector("#o_paw_done_btn");

        var selectedCountry = "TZ";
        var selectedDial = "+255";
        var resendTimer = null;
        var authenticatedData = null;

        // Render SVG flags
        if (flagSvg) flagSvg.innerHTML = FLAG_SVGS[selectedCountry];
        overlay.querySelectorAll("[data-paw-flag-slot]").forEach(function (el) {
            var code = el.getAttribute("data-paw-flag-slot");
            if (FLAG_SVGS[code]) el.innerHTML = FLAG_SVGS[code];
        });

        function clearAlerts() {
            if (errorBox) { errorBox.hidden = true; errorBox.textContent = ""; }
            if (infoBox) { infoBox.hidden = true; infoBox.textContent = ""; }
        }

        function showError(msg) {
            clearAlerts();
            if (errorBox && msg) {
                errorBox.textContent = msg;
                errorBox.hidden = false;
            }
        }

        function showInfo(msg) {
            clearAlerts();
            if (infoBox && msg) {
                infoBox.textContent = msg;
                infoBox.hidden = false;
            }
        }

        function showStep(n) {
            step1.hidden = n !== 1;
            step2.hidden = n !== 2;
            step3.hidden = n !== 3;
            if (n === 1 && phoneInput) setTimeout(function () { phoneInput.focus(); }, 60);
            if (n === 2 && otpInput) setTimeout(function () { otpInput.focus(); }, 60);
        }

        function startResendCountdown(seconds) {
            clearInterval(resendTimer);
            var remaining = Math.max(0, parseInt(seconds || 30, 10));
            if (!resendBtn) return;
            if (remaining <= 0) {
                resendBtn.disabled = false;
                resendBtn.textContent = "Resend the code";
                return;
            }
            resendBtn.disabled = true;
            resendBtn.textContent = "Resend the code (" + remaining + "s)";
            resendTimer = setInterval(function () {
                remaining -= 1;
                if (remaining <= 0) {
                    clearInterval(resendTimer);
                    resendBtn.disabled = false;
                    resendBtn.textContent = "Resend the code";
                } else {
                    resendBtn.textContent = "Resend the code (" + remaining + "s)";
                }
            }, 1000);
        }

        function open(startStep) {
            clearAlerts();
            showStep(startStep || 1);
            overlay.classList.add("is-open");
            overlay.setAttribute("aria-hidden", "false");
            document.body.style.overflow = "hidden";
        }

        function close(wasDismissed) {
            overlay.classList.remove("is-open");
            overlay.setAttribute("aria-hidden", "true");
            document.body.style.overflow = "";
            if (flagMenu) flagMenu.hidden = true;
            if (wasDismissed && !authenticatedData) {
                markDismissed();
            }
            if (authenticatedData && !document.getElementById("grooming-form")) {
                window.location.reload();
            }
        }

        // Flag picker events
        if (flagBtn && flagMenu) {
            flagBtn.addEventListener("click", function (e) {
                e.stopPropagation();
                flagMenu.hidden = !flagMenu.hidden;
            });
            flagMenu.querySelectorAll("[data-paw-country]").forEach(function (opt) {
                opt.addEventListener("click", function () {
                    selectedCountry = opt.getAttribute("data-paw-country");
                    selectedDial = opt.getAttribute("data-paw-dial");
                    if (flagSvg) flagSvg.innerHTML = FLAG_SVGS[selectedCountry] || "";
                    if (dialEl) dialEl.textContent = selectedDial;
                    flagMenu.hidden = true;
                    if (phoneInput) phoneInput.focus();
                });
            });
            document.addEventListener("click", function (e) {
                if (!flagMenu.hidden && !flagMenu.contains(e.target) && !flagBtn.contains(e.target)) {
                    flagMenu.hidden = true;
                }
            });
        }

        // Build full phone number from selected dial code + input
        function buildPhoneValue() {
            var raw = (phoneInput ? phoneInput.value : "").trim();
            if (!raw) return "";
            if (raw.charAt(0) === "+" || raw.indexOf("00") === 0) {
                return raw;
            }
            var digits = raw.replace(/\D/g, "");
            if (digits.charAt(0) === "0") {
                digits = digits.slice(1);
            }
            return selectedDial + digits;
        }

        function handleSendOtp(isResend) {
            var fullPhone = isResend ? "" : buildPhoneValue();
            if (!isResend && !fullPhone) {
                showError("Please enter your phone number.");
                if (phoneInput) phoneInput.focus();
                return;
            }
            clearAlerts();
            var activeBtn = isResend ? resendBtn : sendBtn;
            if (activeBtn) activeBtn.disabled = true;

            jsonRpc("/paw_points/popup/send_otp", {
                phone: fullPhone,
                resend: !!isResend,
                marketing_opt_in: optInInput ? !!optInInput.checked : true
            }).then(function (res) {
                if (sendBtn) sendBtn.disabled = false;
                if (!res.ok) {
                    if (isResend && resendBtn) resendBtn.disabled = false;
                    showError(res.error || "Could not send verification code.");
                    return;
                }
                if (displayPhone) displayPhone.textContent = res.phone || fullPhone;
                showStep(2);
                if (res.message) showInfo(res.message);
                startResendCountdown(res.resend_wait || 30);
            }).catch(function () {
                if (sendBtn) sendBtn.disabled = false;
                if (isResend && resendBtn) resendBtn.disabled = false;
                showError("Network error. Please check your connection and try again.");
            });
        }

        function handleVerifyOtp() {
            var code = (otpInput ? otpInput.value : "").replace(/\s+/g, "");
            if (!code) {
                showError("Please enter the 6-digit verification code.");
                if (otpInput) otpInput.focus();
                return;
            }
            clearAlerts();
            if (verifyBtn) verifyBtn.disabled = true;

            jsonRpc("/paw_points/popup/verify_otp", { otp: code }).then(function (res) {
                if (verifyBtn) verifyBtn.disabled = false;
                if (!res.ok) {
                    if (res.expired) showStep(1);
                    showError(res.error || "Invalid verification code.");
                    return;
                }
                clearInterval(resendTimer);
                authenticatedData = res;

                if (balancePts) balancePts.textContent = res.points_formatted || "0";
                if (balanceVal) {
                    balanceVal.textContent = res.points > 0
                        ? ("Worth " + res.points_value_formatted + " TSh")
                        : "Active Member";
                }
                if (balanceBar) balanceBar.style.width = (res.progress_pct || (res.points > 0 ? 15 : 8)) + "%";
                if (balanceCaption) {
                    if (res.can_redeem) {
                        balanceCaption.textContent = "Ready to redeem 5,000 TSh off your order!";
                        balanceCaption.classList.add("is-ready");
                    } else {
                        var needed = Math.max(1, Math.ceil(100 - (res.points % 100)));
                        balanceCaption.textContent = "Earn " + needed + " more Paw Points to unlock 5,000 TSh off.";
                        balanceCaption.classList.remove("is-ready");
                    }
                }

                showStep(3);

                // Notify Grooming Studio & any other page listeners immediately
                window.dispatchEvent(new CustomEvent("stephans:paw_points_authenticated", { detail: res }));
            }).catch(function () {
                if (verifyBtn) verifyBtn.disabled = false;
                showError("Network error. Please try again.");
            });
        }

        if (sendBtn) sendBtn.addEventListener("click", function () { handleSendOtp(false); });
        if (resendBtn) resendBtn.addEventListener("click", function () { handleSendOtp(true); });
        if (verifyBtn) verifyBtn.addEventListener("click", handleVerifyOtp);

        if (phoneInput) {
            phoneInput.addEventListener("keydown", function (e) {
                if (e.key === "Enter") { e.preventDefault(); handleSendOtp(false); }
            });
        }
        if (otpInput) {
            otpInput.addEventListener("keydown", function (e) {
                if (e.key === "Enter") { e.preventDefault(); handleVerifyOtp(); }
            });
        }

        if (changeNumBtn) {
            changeNumBtn.addEventListener("click", function () {
                clearInterval(resendTimer);
                clearAlerts();
                jsonRpc("/paw_points/popup/reset", {});
                if (otpInput) otpInput.value = "";
                showStep(1);
            });
        }

        if (doneBtn) {
            doneBtn.addEventListener("click", function () { close(false); });
        }

        overlay.querySelectorAll("[data-paw-popup-close]").forEach(function (el) {
            el.addEventListener("click", function () { close(true); });
        });

        overlay.addEventListener("click", function (e) {
            if (e.target === overlay) close(true);
        });

        document.addEventListener("keydown", function (e) {
            if (e.key === "Escape" && overlay.classList.contains("is-open")) {
                close(true);
            }
        });

        // Global click trigger for Cart hint, Grooming Studio hint, Header profile icon, etc.
        document.addEventListener("click", function (e) {
            var trigger = e.target.closest("[data-paw-popup-trigger], [data-open-paw-points='true']");
            if (trigger && !authenticatedData) {
                e.preventDefault();
                open(1);
            }
        });

        // Public API
        window.StephansPawPopup = {
            open: function () { open(1); },
            close: function () { close(true); }
        };

        // Gentle auto-open for guests after 6s (unless dismissed recently)
        if (shouldAutoShowOnPath(window.location.pathname) && !isDismissedRecently()) {
            setTimeout(function () {
                if (!authenticatedData && !overlay.classList.contains("is-open")) {
                    open(1);
                }
            }, 6000);
        }
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", initPawPopup);
    } else {
        initPawPopup();
    }
})();

/**
 * Stephan's Paw Points Interactive Pop-Up Modal
 * Native Odoo 20 Frontend Asset with WhatsApp Authentication,
 * Auto-Account Creation & Duplicate Check Restrictions.
 */
(function () {
  'use strict';

  const FLAG_SVGS = {
    TZ: `<svg width="22" height="15" viewBox="0 0 22 15" class="stephans-flag-svg" xmlns="http://www.w3.org/2000/svg"><clipPath id="tzc_live"><rect width="22" height="15" rx="2"/></clipPath><g clip-path="url(#tzc_live)"><rect width="22" height="15" fill="#1EB53A"/><polygon points="22,0 22,15 0,15" fill="#00A3DD"/><line x1="0" y1="15" x2="22" y2="0" stroke="#FCD116" stroke-width="5.2"/><line x1="0" y1="15" x2="22" y2="0" stroke="#111111" stroke-width="3.2"/></g></svg>`,
    KE: `<svg width="22" height="15" viewBox="0 0 22 15" class="stephans-flag-svg" xmlns="http://www.w3.org/2000/svg"><rect width="22" height="4.5" y="0" fill="#111111"/><rect width="22" height="1" y="4.5" fill="#FFFFFF"/><rect width="22" height="4" y="5.5" fill="#BB0000"/><rect width="22" height="1" y="9.5" fill="#FFFFFF"/><rect width="22" height="4.5" y="10.5" fill="#006600"/><ellipse cx="11" cy="7.5" rx="2" ry="3.4" fill="#BB0000" stroke="#FFFFFF" stroke-width="0.6"/></svg>`,
    UG: `<svg width="22" height="15" viewBox="0 0 22 15" class="stephans-flag-svg" xmlns="http://www.w3.org/2000/svg"><rect width="22" height="2.5" y="0" fill="#111111"/><rect width="22" height="2.5" y="2.5" fill="#FCDC04"/><rect width="22" height="2.5" y="5" fill="#D90000"/><rect width="22" height="2.5" y="7.5" fill="#111111"/><rect width="22" height="2.5" y="10" fill="#FCDC04"/><rect width="22" height="2.5" y="12.5" fill="#D90000"/><circle cx="11" cy="7.5" r="2.2" fill="#FFFFFF"/></svg>`,
    RW: `<svg width="22" height="15" viewBox="0 0 22 15" class="stephans-flag-svg" xmlns="http://www.w3.org/2000/svg"><rect width="22" height="7.5" y="0" fill="#00A1DE"/><rect width="22" height="3.75" y="7.5" fill="#FAD201"/><rect width="22" height="3.75" y="11.25" fill="#20603D"/><circle cx="16.8" cy="3.6" r="1.4" fill="#E5BE01"/></svg>`
  };

  let selectedCountry = 'TZ';
  let selectedDialCode = '+255';
  let timerInterval = null;
  let secondsLeft = 30;
  let currentStep = 'step1';
  let authenticatedUser = null;

  const AUTO_POPUP_DELAY_MS = 20000;
  const POPUP_SEEN_STORAGE_KEY = 'stephans_paw_popup_seen';
  let autoPopupTimer = null;
  let hasAutoPopped = false;

  function markPopupSeen() {
    hasAutoPopped = true;
    try {
      localStorage.setItem(POPUP_SEEN_STORAGE_KEY, 'true');
    } catch (e) {}
  }

  function isPopupSeen() {
    try {
      return localStorage.getItem(POPUP_SEEN_STORAGE_KEY) === 'true';
    } catch (e) {
      return false;
    }
  }

  function jsonRpc(url, params) {
    return fetch(url, {
      method: 'POST',
      credentials: 'same-origin',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
      },
      body: JSON.stringify({
        jsonrpc: '2.0',
        method: 'call',
        params: params || {},
        id: Math.floor(Math.random() * 1e9)
      })
    }).then(resp => resp.json()).then(payload => {
      if (payload && payload.error) {
        const msg = (payload.error.data && payload.error.data.message) || payload.error.message || 'Request failed.';
        return { ok: false, error: msg };
      }
      return (payload && payload.result) || { ok: false, error: 'Unexpected response.' };
    });
  }

  function getElements() {
    return {
      overlay: document.getElementById('paw-modal-overlay'),
      closeBtn: document.getElementById('paw-modal-close'),
      step1: document.getElementById('modal-step-1'),
      step2: document.getElementById('modal-step-2'),
      step3: document.getElementById('modal-step-3'),
      errBox1: document.getElementById('paw-error-box-1'),
      errBox2: document.getElementById('paw-error-box-2'),
      infoBox2: document.getElementById('paw-info-box-2'),
      phoneInput: document.getElementById('paw-phone-input'),
      flagBtn: document.getElementById('flag-picker-btn'),
      flagMenu: document.getElementById('flag-menu'),
      selectedFlag: document.getElementById('selected-flag-svg'),
      selectedDial: document.getElementById('selected-dial-code'),
      optinCheckbox: document.getElementById('paw-optin-checkbox'),
      submitPhoneBtn: document.getElementById('paw-btn-submit-phone'),
      displayPhone: document.getElementById('paw-display-phone'),
      otpInput: document.getElementById('paw-otp-input'),
      resendBtn: document.getElementById('paw-btn-resend'),
      resendTimer: document.getElementById('paw-resend-timer'),
      changeNumberBtn: document.getElementById('paw-btn-change-number'),
      verifyOtpBtn: document.getElementById('paw-btn-verify-otp'),
      cardPoints: document.getElementById('paw-card-points'),
      cardValuePill: document.getElementById('paw-card-value-pill'),
      cardProgress: document.getElementById('paw-card-progress'),
      cardStatusText: document.getElementById('paw-card-progress-text'),
      finishBtn: document.getElementById('paw-btn-finish'),
    };
  }

  function clearAlerts() {
    const els = getElements();
    if (els.errBox1) {
      els.errBox1.style.display = 'none';
      els.errBox1.textContent = '';
    }
    if (els.errBox2) {
      els.errBox2.style.display = 'none';
      els.errBox2.textContent = '';
    }
    if (els.infoBox2) {
      els.infoBox2.style.display = 'none';
      els.infoBox2.textContent = '';
    }
  }

  function showError(stepNum, msg) {
    const els = getElements();
    const box = stepNum === 1 ? els.errBox1 : els.errBox2;
    if (box) {
      box.textContent = msg;
      box.style.display = 'block';
    }
  }

  function setStep(step) {
    const els = getElements();
    if (!els.overlay) return;
    currentStep = step;
    clearAlerts();

    if (els.step1) els.step1.classList.add('stephans-paw-hidden');
    if (els.step2) els.step2.classList.add('stephans-paw-hidden');
    if (els.step3) els.step3.classList.add('stephans-paw-hidden');

    if (step === 'step1') {
      if (els.step1) els.step1.classList.remove('stephans-paw-hidden');
      setTimeout(() => els.phoneInput && els.phoneInput.focus(), 150);
    } else if (step === 'step2') {
      if (els.step2) els.step2.classList.remove('stephans-paw-hidden');
      setTimeout(() => els.otpInput && els.otpInput.focus(), 150);
    } else if (step === 'step3') {
      if (els.step3) els.step3.classList.remove('stephans-paw-hidden');
    }
  }

  function openModal(step) {
    clearTimeout(autoPopupTimer);
    markPopupSeen();
    const els = getElements();
    if (!els.overlay) return;
    els.overlay.classList.remove('stephans-paw-hidden');
    els.overlay.setAttribute('aria-hidden', 'false');
    document.body.style.overflow = 'hidden';
    setStep(step || 'step1');
  }

  function closeModal() {
    markPopupSeen();
    clearTimeout(autoPopupTimer);
    const els = getElements();
    if (!els.overlay) return;
    els.overlay.classList.add('stephans-paw-hidden');
    els.overlay.setAttribute('aria-hidden', 'true');
    document.body.style.overflow = '';
    clearInterval(timerInterval);
    if (els.flagMenu) els.flagMenu.classList.add('stephans-flag-hidden');

    // If authenticated, reload to update global header and shopping state
    if (authenticatedUser) {
      window.location.reload();
    }
  }

  function startAutoPopupTimer() {
    clearTimeout(autoPopupTimer);
    if (document.body.classList.contains('editor_enable') || document.body.classList.contains('editor_has_snippets')) {
      return;
    }
    // Only appear ONCE per browser session/device - never repeat on navigation or reload
    if (isPopupSeen() || hasAutoPopped) {
      return;
    }
    autoPopupTimer = setTimeout(() => {
      const els = getElements();
      if (!els.overlay) return;
      if (els.overlay.classList.contains('stephans-paw-hidden') && !hasAutoPopped && !isPopupSeen()) {
        openModal('step1');
      }
    }, AUTO_POPUP_DELAY_MS);
  }

  function selectCountry(countryCode, dialCode) {
    const els = getElements();
    selectedCountry = countryCode;
    selectedDialCode = dialCode;
    if (els.selectedFlag && FLAG_SVGS[countryCode]) {
      els.selectedFlag.innerHTML = FLAG_SVGS[countryCode];
    }
    if (els.selectedDial) {
      els.selectedDial.textContent = dialCode;
    }
    if (els.flagMenu) {
      els.flagMenu.classList.add('stephans-flag-hidden');
      if (els.flagBtn) els.flagBtn.setAttribute('aria-expanded', 'false');
    }
    if (els.phoneInput) els.phoneInput.focus();
  }

  function startResendTimer(seconds) {
    clearInterval(timerInterval);
    secondsLeft = parseInt(seconds || 30, 10);
    const els = getElements();
    if (els.resendBtn) {
      els.resendBtn.disabled = true;
      els.resendBtn.innerHTML = `Resend the code (<span id="paw-resend-timer">${secondsLeft}</span>s)`;
    }
    timerInterval = setInterval(() => {
      secondsLeft--;
      const timerSpan = document.getElementById('paw-resend-timer');
      if (secondsLeft <= 0) {
        clearInterval(timerInterval);
        if (els.resendBtn) {
          els.resendBtn.disabled = false;
          els.resendBtn.textContent = 'Resend the code';
        }
      } else if (timerSpan) {
        timerSpan.textContent = secondsLeft;
      }
    }, 1000);
  }

  function getCleanedPhoneNumber() {
    const els = getElements();
    const raw = (els.phoneInput && els.phoneInput.value.trim()) || '';
    if (!raw) return '';
    if (raw.startsWith('+') || raw.startsWith('00')) {
      return raw;
    }
    let digits = raw.replace(/\D/g, '');
    if (digits.startsWith('0')) {
      digits = digits.substring(1);
    }
    return `${selectedDialCode}${digits}`;
  }

  function handlePhoneSubmit(isResend) {
    const els = getElements();
    clearAlerts();

    const fullPhone = isResend ? '' : getCleanedPhoneNumber();
    if (!isResend) {
      if (!fullPhone) {
        showError(1, 'Please enter your phone number.');
        els.phoneInput && els.phoneInput.focus();
        return;
      }
      const digitsOnly = fullPhone.replace(/\D/g, '');
      if (digitsOnly.length < 8 || digitsOnly.length > 15) {
        showError(1, 'Please enter a valid phone number (at least 9 digits).');
        els.phoneInput && els.phoneInput.focus();
        return;
      }
    }

    const activeBtn = isResend ? els.resendBtn : els.submitPhoneBtn;
    const originalText = activeBtn ? activeBtn.innerHTML : '';
    if (activeBtn) {
      activeBtn.disabled = true;
      if (!isResend) activeBtn.innerHTML = '<span>Sending code...</span>';
    }

    const optIn = els.optinCheckbox ? els.optinCheckbox.checked : true;

    jsonRpc('/paw_points/popup/send_otp', {
      phone: fullPhone,
      resend: !!isResend,
      marketing_opt_in: optIn
    }).then(res => {
      if (activeBtn && !isResend) {
        activeBtn.disabled = false;
        activeBtn.innerHTML = originalText;
      }

      if (!res.ok) {
        if (isResend && els.resendBtn) els.resendBtn.disabled = false;
        showError(isResend ? 2 : 1, res.error || 'Could not send verification code.');
        return;
      }

      if (els.displayPhone) {
        els.displayPhone.textContent = res.phone || fullPhone;
      }
      setStep('step2');

      if (res.demo_code) {
        if (els.otpInput) {
          els.otpInput.value = res.demo_code;
        }
        if (els.infoBox2) {
          els.infoBox2.innerHTML = `<strong>Note:</strong> ${res.message || 'Verification code: ' + res.demo_code}`;
          els.infoBox2.style.display = 'block';
        }
      } else if (res.message && res.message.includes('offline') && els.infoBox2) {
        els.infoBox2.textContent = res.message;
        els.infoBox2.style.display = 'block';
      }

      startResendTimer(res.resend_wait || 30);
    }).catch(() => {
      if (activeBtn && !isResend) {
        activeBtn.disabled = false;
        activeBtn.innerHTML = originalText;
      }
      if (isResend && els.resendBtn) els.resendBtn.disabled = false;
      showError(isResend ? 2 : 1, 'Network connection error. Please try again.');
    });
  }

  function handleVerifyOtp() {
    const els = getElements();
    clearAlerts();

    const code = (els.otpInput && els.otpInput.value.replace(/\D/g, '')) || '';
    if (!code || code.length !== 6) {
      showError(2, 'Please enter the 6-digit verification code.');
      els.otpInput && els.otpInput.focus();
      return;
    }

    if (els.verifyOtpBtn) {
      els.verifyOtpBtn.disabled = true;
      els.verifyOtpBtn.textContent = 'Verifying...';
    }

    jsonRpc('/paw_points/popup/verify_otp', { otp: code }).then(res => {
      if (els.verifyOtpBtn) {
        els.verifyOtpBtn.disabled = false;
        els.verifyOtpBtn.textContent = 'Continue';
      }

      if (!res.ok) {
        if (res.expired) {
          showError(1, res.error || 'Your verification session expired.');
          setStep('step1');
        } else {
          showError(2, res.error || 'Invalid verification code.');
          els.otpInput && els.otpInput.focus();
        }
        return;
      }

      clearInterval(timerInterval);
      authenticatedUser = res;

      // Update real customer Paw Points in Step 3
      if (els.cardPoints) els.cardPoints.textContent = res.points_formatted || '0';
      if (els.cardValuePill) {
        els.cardValuePill.textContent = res.points > 0 ? `Worth ${res.points_value_formatted} TSh` : 'Active Member';
      }
      if (els.cardProgress) {
        els.cardProgress.style.width = `${res.progress_pct || (res.points > 0 ? 15 : 8)}%`;
      }
      if (els.cardStatusText) {
        if (res.can_redeem) {
          els.cardStatusText.className = 'stephans-paw-card__status stephans-paw-card__status--green';
          els.cardStatusText.textContent = 'Ready to redeem 5,000 TSh off this order!';
        } else {
          const needed = Math.max(1, Math.ceil(100 - (res.points % 100)));
          els.cardStatusText.className = 'stephans-paw-card__status stephans-paw-card__status--muted';
          els.cardStatusText.textContent = `Earn ${needed} more Paw Points to unlock 5,000 TSh off.`;
        }
      }

      setStep('step3');

      // Dispatch global event for listeners (Grooming Studio, Cart)
      window.dispatchEvent(new CustomEvent('stephans:paw_points_authenticated', { detail: res }));
    }).catch(() => {
      if (els.verifyOtpBtn) {
        els.verifyOtpBtn.disabled = false;
        els.verifyOtpBtn.textContent = 'Continue';
      }
      showError(2, 'Network error. Please try again.');
    });
  }

  function init() {
    const els = getElements();
    if (!els.overlay) return;

    if (els.closeBtn) els.closeBtn.addEventListener('click', closeModal);

    els.overlay.addEventListener('click', (e) => {
      if (e.target === els.overlay) closeModal();
    });

    document.querySelectorAll('[data-paw-close-trigger="true"]').forEach(btn => {
      btn.addEventListener('click', closeModal);
    });

    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape' && !els.overlay.classList.contains('stephans-paw-hidden')) {
        closeModal();
      }
    });

    // Flag Picker
    if (els.flagBtn && els.flagMenu) {
      els.flagBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        const isHidden = els.flagMenu.classList.contains('stephans-flag-hidden');
        els.flagMenu.classList.toggle('stephans-flag-hidden');
        els.flagBtn.setAttribute('aria-expanded', isHidden ? 'true' : 'false');
      });

      document.addEventListener('click', (e) => {
        if (!els.flagMenu.contains(e.target) && !els.flagBtn.contains(e.target)) {
          els.flagMenu.classList.add('stephans-flag-hidden');
          els.flagBtn.setAttribute('aria-expanded', 'false');
        }
      });
    }

    document.querySelectorAll('.stephans-flag-option').forEach(btn => {
      btn.addEventListener('click', () => {
        const country = btn.getAttribute('data-country');
        const dial = btn.getAttribute('data-dial');
        selectCountry(country, dial);
      });
    });

    // Step 1: Submit Phone
    if (els.submitPhoneBtn) {
      els.submitPhoneBtn.addEventListener('click', () => handlePhoneSubmit(false));
    }
    if (els.phoneInput) {
      els.phoneInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
          e.preventDefault();
          handlePhoneSubmit(false);
        }
      });
      // Allow only numbers, spaces, and plus
      els.phoneInput.addEventListener('input', (e) => {
        e.target.value = e.target.value.replace(/[^\d\s+]/g, '');
      });
    }

    // Step 2: OTP actions
    if (els.resendBtn) {
      els.resendBtn.addEventListener('click', () => {
        if (!els.resendBtn.disabled) {
          handlePhoneSubmit(true);
        }
      });
    }
    if (els.changeNumberBtn) {
      els.changeNumberBtn.addEventListener('click', () => {
        clearInterval(timerInterval);
        clearAlerts();
        jsonRpc('/paw_points/popup/reset', {});
        if (els.otpInput) els.otpInput.value = '';
        setStep('step1');
      });
    }
    if (els.verifyOtpBtn) {
      els.verifyOtpBtn.addEventListener('click', handleVerifyOtp);
    }
    if (els.otpInput) {
      els.otpInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
          e.preventDefault();
          handleVerifyOtp();
        }
      });
      els.otpInput.addEventListener('input', (e) => {
        e.target.value = e.target.value.replace(/\D/g, '').substring(0, 6);
      });
    }

    // Step 3: Finish
    if (els.finishBtn) {
      els.finishBtn.addEventListener('click', closeModal);
    }

    // Global trigger delegation
    document.addEventListener('click', (e) => {
      const trigger = e.target.closest('[data-open-paw-points], .stephans-paw-points-trigger, a[href="#paw-points"]');
      if (trigger) {
        e.preventDefault();
        openModal('step1');
      }
    });

    window.StephansPawPoints = {
      open: openModal,
      close: closeModal,
      setStep: setStep,
      selectCountry: selectCountry
    };

    startAutoPopupTimer();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();

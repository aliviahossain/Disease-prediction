(function () {
    const form = document.getElementById('profile-form');
    if (!form) return;

    const saveBtn = document.getElementById('profile-save-btn');
    const toastContainer = document.getElementById('profile-toast-container');

    function showToast(message, type) {
        if (!toastContainer || !message) return;
        const toast = document.createElement('div');
        toast.className = `profile-toast profile-toast-${type}`;
        toast.setAttribute('role', 'status');
        toast.innerHTML = `
            <span class="profile-toast-icon" aria-hidden="true">${type === 'success' ? '✓' : '!'}</span>
            <span class="profile-toast-message">${message}</span>
            <button type="button" class="profile-toast-close" aria-label="Dismiss">&times;</button>
        `;
        toastContainer.appendChild(toast);
        const close = () => {
            toast.classList.add('profile-toast-hide');
            setTimeout(() => toast.remove(), 300);
        };
        toast.querySelector('.profile-toast-close').addEventListener('click', close);
        setTimeout(close, 5000);
    }

    document.querySelectorAll('[data-flash]').forEach((el) => {
        showToast(el.dataset.flash, el.dataset.flashType || 'info');
        el.remove();
    });

    function openTab(event, tabId) {
        document.querySelectorAll('.tab-content').forEach((t) => t.classList.remove('active'));
        document.querySelectorAll('.tab-btn').forEach((b) => b.classList.remove('active'));
        document.getElementById(tabId).classList.add('active');
        event.currentTarget.classList.add('active');
    }

    window.openTab = openTab;

    window.calculateBMI = function () {
        const heightEl = document.getElementById('height');
        const weightEl = document.getElementById('weight');
        const bmiEl = document.getElementById('bmi');
        if (!heightEl || !weightEl || !bmiEl) return;
        const h = parseFloat(heightEl.value) / 100;
        const w = parseFloat(weightEl.value);
        if (h > 0 && w > 0) {
            bmiEl.value = (w / (h * h)).toFixed(2);
        } else {
            bmiEl.value = '';
        }
    };

    window.removeNumbers = function (field) {
        field.value = field.value.replace(/[0-9]/g, '');
    };

    function normalizePhoneInput(value) {
        const trimmed = (value || '').trim();
        if (!trimmed) return '';
        if (trimmed.startsWith('+')) return trimmed;
        const digits = trimmed.replace(/\D/g, '');
        if (!digits) return trimmed;
        return `+${digits}`;
    }

    function setFieldError(field, message) {
        const group = field.closest('.form-group');
        if (!group) return;
        let errorEl = group.querySelector('.field-error');
        if (!errorEl) {
            errorEl = document.createElement('span');
            errorEl.className = 'field-error';
            errorEl.setAttribute('role', 'alert');
            group.appendChild(errorEl);
        }
        if (message) {
            field.classList.add('is-invalid');
            errorEl.textContent = message;
        } else {
            field.classList.remove('is-invalid');
            errorEl.textContent = '';
        }
    }

    function clearFieldErrors() {
        form.querySelectorAll('.is-invalid').forEach((el) => el.classList.remove('is-invalid'));
        form.querySelectorAll('.field-error').forEach((el) => {
            el.textContent = '';
        });
    }

    const PHONE_RE = /^\+[1-9][0-9]{7,14}$/;

    function validateProfileForm() {
        clearFieldErrors();
        let valid = true;

        const phone = form.querySelector('[name="phone"]');
        const emergencyPhone = form.querySelector('[name="emergency_phone"]');
        [phone, emergencyPhone].forEach((field) => {
            if (!field || !field.value.trim()) return;
            const normalized = normalizePhoneInput(field.value);
            field.value = normalized;
            if (!PHONE_RE.test(normalized)) {
                setFieldError(
                    field,
                    'Use country code with +, e.g. +15551234567'
                );
                valid = false;
            }
        });

        const address = form.querySelector('[name="address"]');
        if (address && address.value.trim() && address.value.trim().length < 5) {
            setFieldError(address, 'Address must be at least 5 characters.');
            valid = false;
        }

        const dobDay = form.querySelector('[name="dob_day"]');
        const dobMonth = form.querySelector('[name="dob_month"]');
        const dobYear = form.querySelector('[name="dob_year"]');
        const dobParts = [dobDay, dobMonth, dobYear].map((el) => (el ? el.value : ''));
        const anyDob = dobParts.some(Boolean);
        const allDob = dobParts.every(Boolean);
        if (anyDob && !allDob) {
            [dobDay, dobMonth, dobYear].forEach((el) => {
                if (el) setFieldError(el, 'Complete day, month, and year.');
            });
            valid = false;
        }

        if (!valid) {
            showToast('Please fix the highlighted fields before saving.', 'error');
        }
        return valid;
    }

    form.addEventListener('submit', function (event) {
        if (!validateProfileForm()) {
            event.preventDefault();
            return;
        }
        if (!saveBtn) return;
        saveBtn.disabled = true;
        saveBtn.classList.add('is-loading');
        const label = saveBtn.querySelector('.btn-label');
        if (label) label.textContent = 'Saving…';
    });
})();

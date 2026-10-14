/* Normalize localized digits before Frappe evaluates numeric input. */
(() => {
    function normalizeDigits(value) {
        if (typeof value !== "string") return value;
        return value.replace(/[۰-۹٠-٩]/g, (digit) => {
            const code = digit.charCodeAt(0);
            return String(code >= 0x06f0 ? code - 0x06f0 : code - 0x0660);
        });
    }

    frappe.provide("iran_localization");
    iran_localization.normalize_numeric_digits = normalizeDigits;

    const prototype = frappe.ui.form.ControlInt.prototype;
    if (prototype._iran_digits_installed) return;
    const original = prototype.eval_expression;
    prototype.eval_expression = function (value, numberFormat) {
        return original.call(this, normalizeDigits(value), numberFormat);
    };
    prototype._iran_digits_installed = true;
})();

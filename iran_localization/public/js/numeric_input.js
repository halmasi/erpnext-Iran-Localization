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

    const zeroDecimalEnabled = () =>
        Boolean(frappe.boot?.iran_localization?.disable_quantity_and_price_decimals);
    const numericBusinessField = (control) => {
        const name = control.df?.fieldname || "";
        return /(^|_)(qty|quantity|rate|price|amount)($|_)/.test(name);
    };
    const installZeroPrecision = (Control, allFields = false) => {
        if (!Control || Object.hasOwn(Control.prototype, "_iran_zero_precision_installed")) return;
        const originalPrecision = Control.prototype.get_precision;
        Control.prototype.get_precision = function () {
            if (zeroDecimalEnabled() && (allFields || numericBusinessField(this))) return 0;
            return originalPrecision.call(this);
        };
        Control.prototype._iran_zero_precision_installed = true;
    };
    installZeroPrecision(frappe.ui.form.ControlFloat);
    installZeroPrecision(frappe.ui.form.ControlCurrency, true);
})();

import assert from "node:assert/strict";
import fs from "node:fs";
import vm from "node:vm";
import test from "node:test";

const root = new URL("../../../", import.meta.url);
const context = vm.createContext({
    frappe: {
        ui: { form: { ControlData: class {} } },
        utils: { eval_expression: (value) => value },
        provide: () => {},
    },
    iran_localization: {},
    cint: (value, fallback) => Number.isNaN(parseInt(value)) ? fallback : parseInt(value),
    flt: (value) => parseFloat(value),
});
for (const file of [
    "frappe/frappe/public/js/frappe/form/controls/int.js",
    "frappe/frappe/public/js/frappe/form/controls/float.js",
    "frappe/frappe/public/js/frappe/form/controls/currency.js",
    "frappe/frappe/public/js/frappe/form/controls/percent.js",
    "iran_localization/iran_localization/public/js/numeric_input.js",
]) {
    vm.runInContext(fs.readFileSync(new URL(file, root), "utf8"), context);
}

test("Persian, Arabic and mixed digits in actual Frappe numeric controls", () => {
    for (const name of ["ControlInt", "ControlLongInt", "ControlFloat", "ControlCurrency", "ControlPercent"]) {
        const control = new context.frappe.ui.form[name]();
        control.get_number_format = () => undefined;
        control.get_precision = () => 2;
        for (const input of ["۱۲۳۴", "١٢٣٤", "1۲٣4", "1234"]) {
            assert.equal(control.parse(input), 1234, `${name}: ${input}`);
        }
        assert.equal(control.parse("-۱٢"), -12);
        assert.equal(control.parse(""), null);
    }
});

test("decimal currency input and original values are preserved", () => {
    const control = new context.frappe.ui.form.ControlFloat();
    control.get_number_format = () => undefined;
    control.get_precision = () => 2;
    assert.equal(control.parse("۱٢.۳4"), 12.34);
    const normalize = context.iran_localization.normalize_numeric_digits;
    assert.equal(normalize("۲ + ٣"), "2 + 3");
    assert.equal(normalize(0), 0);
    assert.equal(normalize(null), null);
    assert.equal(normalize(undefined), undefined);
});

// Run: node --test iran_localization/tests/test_persian_calendar.mjs
// Loads the installed v16 control methods, rather than recreating their model pipeline.
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import path from "node:path";
import vm from "node:vm";
import { execFileSync } from "node:child_process";
import test from "node:test";
const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../..");
function setup(enabled) {
    const context = vm.createContext({ console, Date, RangeError, Promise, Set });
    context.__ = value => value;
    context.frappe = {
        ui: { form: {} }, boot: { iran_localization: { enable_persian_calendar: enabled } },
        provide() {}, msgprint() {},
        datetime: { nowdate: () => "2026-10-13", validate: value => /^\d{4}-\d{2}-\d{2}$/.test(value) },
        run_serially: async functions => { for (const fn of functions) await fn(); },
    };
    context.$ = value => value;
    const load = file => vm.runInContext(readFileSync(file, "utf8").replace(/^import .*;\n/gm, ""), context, { filename: file });
    for (const file of ["base_control", "base_input", "data", "date", "datetime"]) {
        load(path.resolve(root, "../frappe/frappe/public/js/frappe/form/controls", `${file}.js`));
    }
    const OriginalDate = context.frappe.ui.form.ControlDate;
    const OriginalDatetime = context.frappe.ui.form.ControlDatetime;
    for (const file of ["conversion", "date_control"]) load(path.join(root, "iran_localization/public/js/persian_calendar", `${file}.js`));
    return { context, ns: context.iran_persian_calendar, OriginalDate, OriginalDatetime };
}
function control(context, value = "2026-10-13") {
    const c = Object.create(context.frappe.ui.form.ControlDate.prototype);
    const input = { value: "", val(value) { if (arguments.length) { this.value = value; return this; } return this.value; }, attr() { return this; } };
    Object.assign(c, { df: { fieldname: "date", fieldtype: "Date" }, doc: { date: value }, value, $input: input,
        set_mandatory() {}, set_invalid() {}, get_status: () => "Write" });
    c.set_input(value);
    return c;
}
test("disabled leaves both constructors untouched", () => {
    const { context, OriginalDate, OriginalDatetime } = setup(false);
    assert.equal(context.frappe.ui.form.ControlDate, OriginalDate);
    assert.equal(context.frappe.ui.form.ControlDatetime, OriginalDatetime);
});
test("enabled subclasses Date, preserves Datetime, and uninstalls", () => {
    const { context, ns, OriginalDate, OriginalDatetime } = setup(true);
    assert.equal(Object.getPrototypeOf(context.frappe.ui.form.ControlDate.prototype), OriginalDate.prototype);
    assert.equal(context.frappe.ui.form.ControlDatetime, OriginalDatetime);
    ns.uninstall();
    assert.equal(context.frappe.ui.form.ControlDate, OriginalDate);
});
test("Gregorian load and refresh only change display", () => {
    const { context } = setup(true); const c = control(context);
    assert.equal(c.$input.val(), "1405/07/21"); assert.equal(c.doc.date, "2026-10-13");
    c.set_input(c.doc.date); assert.equal(c.$input.val(), "1405/07/21");
});
test("manual Persian/Arabic digits travel through real model pipeline", async () => {
    const { context } = setup(true); const c = control(context);
    await c.parse_validate_and_set_in_model("۱۴۰۵/۰۷/۲۲");
    assert.equal(c.doc.date, "2026-10-14"); assert.equal(c.$input.val(), "1405/07/22");
    c.$input.val("١٤٠٥/٠٧/٢٣"); assert.equal(c.get_value(), "2026-10-15");
});
test("clear and new document", async () => {
    const { context } = setup(true); const c = control(context, "");
    assert.equal(c.$input.val(), "");
    await c.parse_validate_and_set_in_model("1405/07/21");
    await c.parse_validate_and_set_in_model("");
    assert.equal(c.doc.date, ""); assert.equal(c.$input.val(), "");
});
test("programmatic set_value and picker selection stay Gregorian", async () => {
    const { context, ns } = setup(true); const c = control(context);
    await c.set_value(ns.jalaliToGregorian("1405/08/01"));
    assert.equal(c.doc.date, "2026-10-23"); assert.equal(c.$input.val(), "1405/08/01");
});
test("invalid input retains original value and sets invalid", async () => {
    const { context } = setup(true); const c = control(context);
    await c.parse_validate_and_set_in_model("1404/12/30");
    assert.equal(c.doc.date, "2026-10-13"); assert.equal(c.df.invalid, true);
    await c.parse_validate_and_set_in_model("1405/07/22"); assert.equal(c.df.invalid, false);
});
test("date bounds and disabled dates reject picker/manual values", async () => {
    const { context, ns } = setup(true); const c = control(context);
    c.df.min_date = "2026-10-13"; c.df.max_date = "2026-10-15"; c.df.disabled_dates = ["2026-10-14"];
    for (const value of ["1405/07/20", "1405/07/22", "1405/07/24"]) {
        await c.parse_validate_and_set_in_model(value); assert.equal(c.doc.date, "2026-10-13");
    }
    assert.equal(ns.isAllowed(c, "2026-10-15"), true);
});
test("conversion rejects impossible dates and handles leap boundaries", () => {
    const { ns } = setup(true);
    assert.equal(ns.jalaliToGregorian("1403/12/30"), "2025-03-20");
    assert.equal(ns.gregorianToJalali("2026-03-21"), "1405/01/01");
    for (const value of ["1404/12/30", "1405/13/01", "1405/01/32", "1405/07/31", "1405/01/00", "junk"]) assert.throws(() => ns.jalaliToGregorian(value), RangeError);
    for (const value of ["2025-02-29", "2026-13-01", "2026-01-00", "2026-04-31"]) assert.throws(() => ns.gregorianToJalali(value), RangeError);
    for (const value of [null, undefined, ""]) { assert.equal(ns.gregorianToJalali(value), ""); assert.equal(ns.jalaliToGregorian(value), ""); }
});
test("every day from 1390 through 1410 round trips", () => {
    const { ns } = setup(true);
    for (let year = 1390; year <= 1410; year++) for (let month = 1; month <= 12; month++) for (let day = 1; day <= ns.monthLength(year, month); day++) {
        const value = ns.format(year, month, day, "/"); assert.equal(ns.gregorianToJalali(ns.jalaliToGregorian(value)), value);
    }
});

test("JS agrees with the existing Python calendar across every supported year", () => {
    const { ns } = setup(true);
    const script = `import json,jdatetime
samples=[]
for year in range(1,9378):
 for month,day in [(1,1),(12,29)]+([(12,30)] if jdatetime.date(year,1,1).isleap() else []):
  value=jdatetime.date(year,month,day)
  samples.append([f"{year:04d}/{month:02d}/{day:02d}",value.togregorian().isoformat()])
print(json.dumps(samples))`;
    const samples = JSON.parse(execFileSync(path.resolve(root, "../../env/bin/python"), ["-c", script], { encoding: "utf8", maxBuffer: 4 * 1024 * 1024 }));
    for (const [jalali, gregorian] of samples) {
        assert.equal(ns.jalaliToGregorian(jalali), gregorian);
        assert.equal(ns.gregorianToJalali(gregorian), jalali);
    }
});

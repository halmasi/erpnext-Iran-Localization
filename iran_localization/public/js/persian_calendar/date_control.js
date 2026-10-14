(() => {
    const ns = globalThis.iran_persian_calendar;
    ns.isAllowed = (control, value) => {
        const options = { minDate: control.df.min_date, maxDate: control.df.max_date, ...control.get_df_options() };
        const iso = date => date instanceof Date ? ns.format(date.getFullYear(), date.getMonth() + 1, date.getDate(), "-") : date;
        return (!options.minDate || value >= iso(options.minDate)) &&
            (!options.maxDate || value <= iso(options.maxDate)) && !(control.df.disabled_dates || []).includes(value);
    };
    ns.install = () => {
        if (!frappe.boot?.iran_localization?.enable_persian_calendar || ns.originalDate) return;
        const OriginalDate = frappe.ui.form.ControlDate;
        if (!OriginalDate) return;
        ns.originalDate = OriginalDate;
        // Replace only the Date constructor. Existing Datetime/Time prototypes are untouched.
        frappe.ui.form.ControlDate = class PersianDate extends OriginalDate {
            make_picker() {
                this.$input.attr({ placeholder: "YYYY/MM/DD", "aria-haspopup": "dialog", "aria-expanded": "false" });
                this.$input.on("focus.iranCalendar click.iranCalendar", () => ns.getPicker().show(this));
                this.$input.on("keydown.iranCalendar", e => {
                    if (e.key === "Escape" || e.key === "Tab") ns.getPicker().hide();
                    if (e.key === "ArrowDown") {
                        ns.getPicker().show(this);
                        ns.getPicker().$popup.find("button[data-day]:not(:disabled)").first().trigger("focus");
                        e.preventDefault();
                    }
                });
                this.set_t_for_today();
            }
            set_formatted_input(value) {
                if (value === "Today") value = frappe.datetime.nowdate();
                frappe.ui.form.ControlData.prototype.set_formatted_input.call(this, value);
            }
            format_for_input(value) { return ns.gregorianToJalali(value); }
            set_disp_area(value) {
                if (this.disp_area) $(this.disp_area).text(ns.gregorianToJalali(value));
            }
            parse(value) {
                try {
                    const result = ns.jalaliToGregorian(value);
                    if (result && !ns.isAllowed(this, result)) throw new RangeError("Date is outside allowed dates");
                    this.df.invalid = false;
                    this.$input?.attr("aria-invalid", "false");
                    return result;
                } catch (error) {
                    if (!(error instanceof RangeError)) throw error;
                    this.df.invalid = true;
                    this.$input?.attr("aria-invalid", "true");
                    this.set_invalid?.();
                    return this.get_model_value() || this.value || "";
                }
            }
            parse_validate_and_set_in_model(value, event) {
                const parsed = this.parse(value);
                if (this.df.invalid) {
                    frappe.msgprint(__("Enter a valid Jalali date in YYYY/MM/DD format within the allowed dates."));
                    return Promise.resolve();
                }
                return this.validate_and_set_in_model(parsed, event);
            }
        };
    };
    ns.uninstall = () => {
        if (ns.originalDate) frappe.ui.form.ControlDate = ns.originalDate;
        delete ns.originalDate;
        ns.picker?.hide();
        // Existing controls retain their class; reload Desk after changing settings.
    };
    // app_include_js runs after desk.bundle; boot is already present in desk.html.
    ns.install();
})();

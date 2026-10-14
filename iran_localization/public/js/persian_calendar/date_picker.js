(() => {
    const ns = globalThis.iran_persian_calendar;
    const months = ["فروردین", "اردیبهشت", "خرداد", "تیر", "مرداد", "شهریور", "مهر", "آبان", "آذر", "دی", "بهمن", "اسفند"];
    // One shared popup avoids retaining a document listener for every field/grid row.
    class Picker {
        constructor() {
            this.$popup = $('<div class="iran-jalali-picker" role="dialog" aria-label="تقویم شمسی" hidden></div>').appendTo(document.body);
            // Keep the input focused and prevent filter popovers from treating picker clicks as outside clicks.
            this.$popup.on("mousedown", e => { e.preventDefault(); e.stopPropagation(); });
            this.$popup.on("click", "button", e => {
                const button = e.currentTarget;
                if (button.dataset.day) this.select(ns.format(this.year, this.month, Number(button.dataset.day), "/"));
                else if (button.dataset.move) this.move(Number(button.dataset.move));
                else if (button.dataset.action === "today") this.select(ns.gregorianToJalali(frappe.datetime.nowdate()));
                else if (button.dataset.action === "clear") this.select("");
            });
            $(document).on("mousedown.iranCalendar", e => {
                if (this.control && !this.$popup[0].contains(e.target) && e.target !== this.control.input) this.hide();
            });
            $(window).on("resize.iranCalendar scroll.iranCalendar", () => this.hide());
            document.addEventListener("scroll", () => this.hide(), true);
            frappe.router?.on("change", () => this.hide());
            document.addEventListener("focusin", e => {
                if (this.control && e.target !== this.control.input && !this.$popup[0].contains(e.target)) this.hide();
            });
            this.$popup.on("keydown", e => {
                if (e.key === "Escape") { this.control?.input.focus(); this.hide(); e.preventDefault(); }
            });
        }
        show(control) {
            this.control = control;
            const value = control.value || frappe.datetime.nowdate();
            [this.year, this.month, this.day] = ns.gregorianToJalali(value).split("/").map(Number);
            this.render();
            const rect = control.input.getBoundingClientRect();
            this.$popup.prop("hidden", false);
            const height = this.$popup.outerHeight();
            const width = this.$popup.outerWidth();
            this.$popup.css({
                top: rect.bottom + height + 8 > window.innerHeight && rect.top > height ? rect.top - height - 8 : rect.bottom + 8,
                left: Math.max(8, Math.min(rect.left, window.innerWidth - width - 8)),
            });
            control.$input.attr("aria-expanded", "true");
        }
        hide() {
            this.$popup.prop("hidden", true);
            this.control?.$input.attr("aria-expanded", "false");
            this.control = null;
        }
        move(direction) {
            let month = this.month + direction, year = this.year;
            if (month === 0) { month = 12; year--; }
            if (month === 13) { month = 1; year++; }
            if (year < 1 || year > 9377) return;
            this.year = year;
            this.month = month;
            this.render();
        }
        select(value) {
            const control = this.control;
            const gregorian = value ? ns.jalaliToGregorian(value) : "";
            if (gregorian && !ns.isAllowed(control, gregorian)) return;
            this.hide();
            // set_value is a model API: it takes Gregorian, never the display string.
            control.set_value(gregorian);
        }
        render() {
            const $p = this.$popup.empty();
            const $header = $('<div class="iran-jalali-header"></div>').appendTo($p);
            $('<button type="button" class="btn btn-default btn-xs" aria-label="ماه قبل" data-move="-1">‹</button>').appendTo($header);
            $('<span aria-live="polite"></span>').text(`${months[this.month - 1]} ${this.year}`).appendTo($header);
            $('<button type="button" class="btn btn-default btn-xs" aria-label="ماه بعد" data-move="1">›</button>').appendTo($header);
            const $grid = $('<div class="iran-jalali-grid"></div>').appendTo($p);
            ["شنبه", "یکشنبه", "دوشنبه", "سه‌شنبه", "چهارشنبه", "پنجشنبه", "جمعه"].forEach(label => $('<span class="text-muted"></span>').text(label).appendTo($grid));
            const first = ns.jalaliToGregorian(ns.format(this.year, this.month, 1, "/"));
            const weekday = (new Date(first + "T00:00:00Z").getUTCDay() + 1) % 7;
            for (let i = 0; i < weekday; i++) $('<span></span>').appendTo($grid);
            for (let day = 1; day <= ns.monthLength(this.year, this.month); day++) {
                const jalali = ns.format(this.year, this.month, day, "/");
                const gregorian = ns.jalaliToGregorian(jalali);
                const selected = gregorian === this.control.value;
                $('<button type="button" class="btn btn-xs"></button>')
                    .attr({ "data-day": day, "aria-label": jalali, "aria-pressed": String(selected) })
                    .toggleClass("btn-primary", selected).prop("disabled", !ns.isAllowed(this.control, gregorian))
                    .text(day).appendTo($grid);
            }
            const $footer = $('<div class="iran-jalali-footer"></div>').appendTo($p);
            $('<button type="button" class="btn btn-default btn-xs" data-action="today">امروز</button>').appendTo($footer);
            $('<button type="button" class="btn btn-default btn-xs" data-action="clear">پاک کردن</button>').appendTo($footer);
        }
    }
    ns.getPicker = () => ns.picker || (ns.picker = new Picker());
})();

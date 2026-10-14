/* Deterministic day arithmetic matching the existing jdatetime 33-year calendar.
 * Original implementation; no browser locale or remote dependency.
 */
(() => {
    const ns = globalThis.iran_persian_calendar = globalThis.iran_persian_calendar || {};
    const DAY = 86400000;
    const leapResidues = new Set([1, 5, 9, 13, 17, 22, 26, 30]);
    const leap = year => leapResidues.has(year % 33);
    const starts = [0];
    for (let year = 1; year <= 9377; year++) {
        starts[year] = starts[year - 1] + 365 + Number(leap(year));
    }
    const epoch = Date.UTC(1600, 2, 20) / DAY - starts[978];
    const normalizeDigits = value => value == null ? "" : String(value).trim().replace(/[۰-۹٠-٩]/g,
        digit => String("۰۱۲۳۴۵۶۷۸۹".includes(digit) ? "۰۱۲۳۴۵۶۷۸۹".indexOf(digit) : "٠١٢٣٤٥٦٧٨٩".indexOf(digit)));
    function parts(value, separator) {
        const match = normalizeDigits(value).match(separator === "/" ? /^(\d{4})\/(\d{1,2})\/(\d{1,2})$/ : /^(\d{4})-(\d{1,2})-(\d{1,2})$/);
        if (!match) throw new RangeError("Expected YYYY/MM/DD (Jalali) or YYYY-MM-DD (Gregorian)");
        return match.slice(1).map(Number);
    }
    function monthLength(year, month) {
        if (!Number.isInteger(year) || year < 1 || year > 9377 || !Number.isInteger(month) || month < 1 || month > 12) {
            throw new RangeError("Date outside supported calendar range");
        }
        return month <= 6 ? 31 : month <= 11 ? 30 : leap(year) ? 30 : 29;
    }
    const format = (year, month, day, sep) => [year.toString().padStart(4, "0"), month.toString().padStart(2, "0"), day.toString().padStart(2, "0")].join(sep);
    function jalaliToGregorian(value) {
        if (value == null || value === "") return "";
        const [year, month, day] = parts(value, "/");
        if (day < 1 || day > monthLength(year, month)) throw new RangeError("Invalid Jalali day");
        const offset = month <= 7 ? (month - 1) * 31 : 186 + (month - 7) * 30;
        const result = new Date((epoch + starts[year - 1] + offset + day - 1) * DAY);
        if (result.getUTCFullYear() > 9999) throw new RangeError("Gregorian year exceeds 9999");
        return format(result.getUTCFullYear(), result.getUTCMonth() + 1, result.getUTCDate(), "-");
    }
    function gregorianToJalali(value) {
        if (value == null || value === "") return "";
        const [year, month, day] = parts(value, "-");
        const result = new Date(0);
        result.setUTCFullYear(year, month - 1, day);
        if (year < 1 || month < 1 || month > 12 || day < 1 || result.getUTCFullYear() !== year || result.getUTCMonth() + 1 !== month || result.getUTCDate() !== day) {
            throw new RangeError("Invalid Gregorian date");
        }
        let offset = result.getTime() / DAY - epoch;
        if (offset < 0 || offset >= starts[9377]) throw new RangeError("Date outside supported calendar range");
        let low = 1, high = 9377;
        while (low < high) {
            const middle = Math.ceil((low + high) / 2);
            if (starts[middle - 1] <= offset) low = middle;
            else high = middle - 1;
        }
        offset -= starts[low - 1];
        const jalaliMonth = offset < 186 ? Math.floor(offset / 31) + 1 : Math.floor((offset - 186) / 30) + 7;
        const jalaliDay = offset < 186 ? offset % 31 + 1 : (offset - 186) % 30 + 1;
        return format(low, jalaliMonth, jalaliDay, "/");
    }
    Object.assign(ns, { normalizeDigits, gregorianToJalali, jalaliToGregorian, monthLength, format });
})();

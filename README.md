# بومی‌سازی ایران برای ERPNext

افزونهٔ ماژولار بومی‌سازی ایران برای `ERPNext` و نسخه‌های ۱۵ و ۱۶ از `Frappe`.
هدف این پروژه اضافه‌کردن قابلیت‌های موردنیاز کسب‌وکارهای ایرانی به `ERPNext` است، بدون اینکه هستهٔ اصلی `ERPNext` تغییر کند. تمام فیلدها، تنظیمات، سرویس‌ها و منطق اختصاصی داخل همین افزونه نگهداری می‌شوند.

> نسخهٔ فعلی: `0.2.0`  
> نسخه‌های آزمایش‌شده: `Frappe 15.121.3 / 16.51.1` و `ERPNext 15.121.6 / 16.50.0`

برای توضیح کامل کار با ماژول‌ها، [راهنمای فارسی](docs/USER_GUIDE_FA.md) را ببینید.

---

## امکانات

| ماژول | امکانات | کلید فعال‌سازی |
|---|---|---|
| اطلاعات ایران | شناسه ملی، کد اقتصادی، شماره ثبت و کد پستی شرکت، مشتری و تأمین‌کننده | همیشه در دسترس |
| اعتبارسنجی | تبدیل ارقام فارسی و عربی، کنترل قالب و کنترل اختیاری رقم کنترل | `enable_core_validation` |
| قیمت‌گذاری | به‌روزرسانی هزینهٔ `BOM` و قیمت فروش، پشتیبانی از `BOM` چندسطحی، شاخه‌های مشترک و تشخیص چرخه | `enable_pricing_automation` |
| صورتحساب رسمی | ذخیره مشخصات طرفین، چاپ فارسی راست‌به‌چپ و تاریخ شمسی | `enable_official_invoice_module` |
| پیامک | صف و سابقهٔ درخواست، ارائه‌دهندهٔ آزمایشی و کاوه‌نگار | `enable_sms` |
| سامانهٔ مؤدیان | صف مستقل از حسابداری، ارائه‌دهندهٔ آزمایشی و درگاه `HTTP` قابل تعویض | `enable_taxpayer_system` |
| فروشگاه و `API` | کاتالوگ منتخب، محاسبهٔ قیمت و مالیات در سمت سرور و ایجاد سفارش پیش‌نویس | `enable_commerce_api` |

ماژول‌های اختیاری در نصب جدید خاموش هستند. مقادیر مخصوص هر سایت، مانند `Price List`، شرکت، مشتری و ارائه‌دهنده، برای هر سایت به‌صورت جداگانه تنظیم می‌شوند.

---

# نصب

## پیش‌نیازها

قبل از نصب، موارد زیر باید آماده باشند:

- `Frappe / ERPNext` نسخهٔ ۱۵ یا ۱۶
- یک `Bench` فعال
- یک سایت که `ERPNext` روی آن نصب شده باشد
- `Git`
- دسترسی به ترمینال سرور یا `Dev Container`

برای بررسی نسخه‌ها:

```bash
bench version
```

---

## نصب مستقیم از GitHub

از پوشهٔ `Bench` اجرا کنید:

```bash
cd /path/to/frappe-bench
```

برای دریافت افزونه:

```bash
bench get-app https://github.com/halmasi/erpnext-Iran-Localization.git
```

اگر می‌خواهید شاخهٔ توسعه را نصب کنید:

```bash
bench get-app --branch develop https://github.com/halmasi/erpnext-Iran-Localization.git
```

سپس افزونه را روی سایت نصب کنید:

```bash
bench --site YOUR_SITE install-app iran_localization
```

مثال:

```bash
bench --site erp.localhost install-app iran_localization
```

بعد از نصب، مهاجرت پایگاه داده و ساخت فایل‌های افزونه را اجرا کنید:

```bash
bench --site YOUR_SITE migrate
bench build --app iran_localization
```

برای بررسی نصب:

```bash
bench --site YOUR_SITE list-apps
```

باید `iran_localization` را در خروجی ببینید.

---

## نصب از مسیر محلی

اگر سورس افزونه را روی سیستم خود دارید:

```bash
bench get-app /absolute/path/to/iran_localization
bench --site YOUR_SITE install-app iran_localization
bench --site YOUR_SITE migrate
bench build --app iran_localization
```

---

# تنظیم اولیه پس از نصب

در `ERPNext` وارد فضای کاری زیر شوید:

```text
Iran Localization
```

سپس صفحهٔ تنظیمات زیر را باز کنید:

```text
Iran Localization Settings
```

برای شروع پیشنهاد می‌شود:

```text
Core Validation        ON
Pricing Automation     OFF
Official Invoice       OFF
SMS                    OFF
Taxpayer System        OFF
Commerce API           OFF
```

هر ماژول را فقط پس از تکمیل تنظیمات موردنیاز آن فعال کنید.

---

# ارتقای افزونه

پیش از ارتقا از سایت و فایل‌ها نسخهٔ پشتیبان تهیه کنید:

```bash
bench --site YOUR_SITE backup --with-files
```

سپس وارد پوشهٔ افزونه شوید:

```bash
cd /path/to/frappe-bench/apps/iran_localization
git pull
cd ../..
```

وابستگی‌های `Python` را به‌روزرسانی کنید:

```bash
./env/bin/python -m pip install -e apps/iran_localization
```

سپس:

```bash
bench --site YOUR_SITE migrate
bench build --app iran_localization
bench --site YOUR_SITE clear-cache
```

---

# حذف افزونه

پیش از حذف، از سایت نسخهٔ پشتیبان تهیه کنید.

برای حذف افزونه از یک سایت:

```bash
bench --site YOUR_SITE uninstall-app iran_localization
```

پس از حذف از سایت، در صورت نیاز می‌توانید سورس افزونه را نیز از `Bench` حذف کنید.

---

# تنظیمات و Fixtures

ساختار تنظیمات افزونه به‌صورت `DocType` استاندارد نگهداری می‌شود.

مقادیر مخصوص هر سایت، مانند موارد زیر، نباید داخل `fixture` عمومی پروژه قرار بگیرند:

- `Price List`
- شرکت
- مشتری
- کلید `API`
- تنظیمات ارائه‌دهنده‌ها

دستور `export-fixtures` فقط باید ساختارهای قابل‌انتقال افزونه را صادر کند و نه تنظیمات واقعی یک شرکت.

---

# قیمت‌گذاری خودکار

برای فعال‌سازی قیمت‌گذاری خودکار:

1. `Price List` مواد اولیه را انتخاب کنید.
2. `Price List` فروش محصولات را انتخاب کنید.
3. درصد سربار را تعیین کنید.
4. درصد سود را تعیین کنید.
5. گزینهٔ `Pricing Automation` را فعال کنید.

`Price List` مواد اولیه و `Price List` فروش محصولات باید متفاوت و فعال باشند.

فرمول فعلی:

```text
قیمت واحد = (هزینه کل BOM / مقدار خروجی BOM)
           × (1 + سربار / 100)
           × (1 + حاشیه سود / 100)
```

`BOM`های ثبت‌شده و نهایی‌شده به‌روزرسانی می‌شوند و وابستگی‌های چندسطحی نیز در زنجیرهٔ محصولات اعمال می‌شوند. در صورت وجود چرخه، عملیات با خطای مشخص متوقف می‌شود.

قیمت‌های اختصاصی مشتری، تأمین‌کننده، `Batch` یا قیمت‌های آینده بازنویسی نمی‌شوند.

---

# صورتحساب فارسی

برای استفاده:

1. ماژول صورتحساب رسمی را فعال کنید.
2. در `Sales Invoice` گزینهٔ «صورتحساب رسمی ایران» را فعال کنید.
3. اطلاعات ثبتی طرفین را تکمیل کنید.

قالب چاپ:

```text
Iran Official Invoice
```

این قالب از مبالغ، مالیات‌ها و روش گرد کردن خود `ERPNext` استفاده می‌کند.

> چاپ صورتحساب فارسی به‌معنی تأیید یا پذیرش آن در سامانهٔ مؤدیان نیست.

---

# پیامک و سامانهٔ مؤدیان

ارائه‌دهندهٔ موردنظر را از بخش تنظیمات انتخاب کنید.

ارائه‌دهندهٔ `mock` فقط برای آزمایش است و ارسال واقعی انجام نمی‌دهد.

برای استفاده از کاوه‌نگار، مقادیر زیر لازم هستند:

```text
sms_api_key
sms_sender
```

ماژول سامانهٔ مؤدیان از عملیات عادی `ERP` جدا نگه داشته شده است. خاموش بودن یا خرابی این ماژول نباید مانع عملیات عادی فروش، خرید، حسابداری یا صدور فاکتور شود.

وضعیت‌های ممکن درخواست:

```text
Pending
Sent
Simulated
Unknown
Failed
```

وضعیت `Sent` فقط به‌معنی پذیرش درخواست توسط ارائه‌دهنده است و الزاماً نشان‌دهندهٔ پذیرش نهایی مالیاتی نیست.

---

# API فروشگاه

این `API` برای بخش پشتی سامانه و با کاربر احراز هویت‌شدهٔ `Frappe` طراحی شده است. کلید `API` را در مرورگر یا رابط کاربری عمومی قرار ندهید.

کاربر `API` باید نقش و مجوز مناسب داشته باشد؛ برای مثال:

```text
Sales User
Sales Manager
System Manager
```

فقط کالاهایی که مقدار زیر برای آن‌ها فعال باشد در کاتالوگ نمایش داده می‌شوند:

```text
iran_publish_to_commerce = 1
```

مسیرهای فعلی:

| روش | مسیر `/api/method/` |
|---|---|
| `GET` | `iran_localization.modules.commerce.api.catalog` |
| `POST` | `iran_localization.modules.commerce.api.quote` |
| `POST` | `iran_localization.modules.commerce.api.create_order` |

نمونهٔ درخواست:

```json
{
  "items": [
    {
      "item_code": "YOUR_ITEM",
      "qty": 2
    }
  ],
  "delivery_date": "2026-12-01",
  "request_id": "order-client-0001"
}
```

قیمت و مالیات در سمت `ERPNext` محاسبه می‌شوند.

استفادهٔ دوباره از همان `request_id` باید همان سفارش قبلی را برگرداند. تغییر محتوای درخواست با همان شناسه، خطا محسوب می‌شود.

---

# تست و توسعه

برای اجرای تست‌ها روی سایت آزمایشی:

```bash
./env/bin/python apps/iran_localization/scripts/run_tests.py --site YOUR_TEST_SITE
```

برای بررسی کد:

```bash
ruff check apps/iran_localization/iran_localization
```

برای بررسی قالب‌بندی:

```bash
ruff format --check apps/iran_localization/iran_localization
```

تست‌ها شامل مواردی مانند این‌ها هستند:

- ساختار تنظیمات
- حفظ مقادیر تنظیمات
- اعتبارسنجی
- `BOM` مستقیم
- `BOM` چندسطحی
- شاخه‌های مشترک
- تشخیص چرخه
- ایجاد و به‌روزرسانی `Item Price`
- کنترل مجوزها
- جلوگیری از ثبت تکراری درخواست‌ها
- پیامک آزمایشی
- مؤدیان آزمایشی
- پاسخ نامشخص
- چاپ فارسی

`API`های واقعی در تست‌ها شبیه‌سازی می‌شوند.

---

# ساختار ماژولار

ساختار کلی پروژه:

```text
iran_localization/
├── modules/
│   ├── core/
│   ├── pricing/
│   ├── official_invoice/
│   ├── taxpayer/
│   ├── sms/
│   └── commerce/
├── fixtures/
├── patches/
├── hooks.py
└── ...
```

هر قابلیت باید تا حد امکان مستقل، قابل تست و قابل فعال یا غیرفعال‌سازی باشد.

---

# اصول طراحی

- عدم تغییر مستقیم هستهٔ `ERPNext`
- قابلیت نصب روی پروژه‌های دیگر
- نگهداری تنظیمات به‌صورت مخصوص هر سایت
- ماژولار بودن قابلیت‌ها
- اختیاری بودن اتصال به سامانهٔ مؤدیان
- مستقل بودن عملیات عادی `ERP` از سرویس‌های بیرونی
- امکان اضافه‌کردن ارائه‌دهنده‌های جدید
- حفظ سازگاری با ارتقاهای آینده تا حد ممکن

---

# وضعیت فعلی پروژه

تست کامل سازگاری روی `ERPNext 16.50.0` و `Frappe 16.51.1`:

- ۳۸ تست اجرا شد
- ۳۸ تست پاس شد
- ۰ خطا
- ۰ تست رد شد

نسخهٔ فعلی:

```text
0.2.0
```

نسخه‌های آزمایش‌شده:

```text
Frappe 15.121.3 / 16.51.1
ERPNext 15.121.6 / 16.50.0
```

مواردی که پیش از انتشار پایدار باید بررسی شوند:

- نصب روی یک سایت کاملاً جدید
- راه‌اندازی مجدد واقعی `Dev Container` یا محیط عملیاتی
- نصب و ارتقا روی محیط تمیز
- آزمایش ارائه‌دهندهٔ واقعی پیامک
- آزمایش درگاه واقعی سامانهٔ مؤدیان
- استقرار در محیط عملیاتی

---

# مشارکت

ارسال `Issue` و `Pull Request` برای موارد زیر خوش‌آمد است:

- رفع باگ
- بهبود ترجمه
- افزودن ارائه‌دهندهٔ جدید
- بهبود سازگاری با `ERPNext`
- توسعهٔ قابلیت‌های بومی ایران

---

# منابع

- [Kavenegar REST API](https://kavenegar.github.io/kavenegar_en/)
- [Persian Tools — Legal ID validation](https://github.com/persian-tools/persian-tools/blob/master/src/modules/legalId/index.ts)
- [Iranian National ID validator](https://github.com/hamed-zeidabadi/iranian-national-id-validator)
- [jdatetime](https://pypi.org/project/jdatetime/)

---

# مجوز

`MIT`

## تقویم شمسی / Persian Calendar

تقویم شمسی اختیاری است و در نصب جدید خاموش است. در **Iran Localization Settings**، گزینهٔ **فعال‌سازی تقویم شمسی** (`enable_persian_calendar`) را فعال کنید و ذخیره کنید؛ Desk دوباره بارگذاری می‌شود. فیلدهای استاندارد `Date` در فرم، ردیف‌های جدول قابل ویرایش، دیالوگ و فیلترهای استاندارد لیست و گزارش با قالب `YYYY/MM/DD` نمایش داده می‌شوند. ورود ارقام فارسی، عربی و انگلیسی، انتخاب روز، ماه قبل/بعد، امروز و پاک کردن پشتیبانی می‌شود. هفته از شنبه آغاز می‌شود. تغییر این تنظیم فقط نمایش و ورود تاریخ را تغییر می‌دهد؛ دیتابیس، API و منطق حسابداری همچنان میلادی هستند.

This optional feature targets **Frappe/ERPNext v16**. Enable **فعال‌سازی تقویم شمسی** in **Iran Localization Settings** and save; Desk reloads. Standard `Date` controls use a local Jalali picker and manual `YYYY/MM/DD` input, including English, Persian and Arabic digits. This covers form and editable grid fields, dialogs, and list/query report filters built with standard Date controls. `2026-10-13` displays as `1405/07/21`; entering that Jalali date stores `2026-10-13`. Disable and save to restore standard Frappe controls. Other users should reload Desk after the site setting changes.

**Limitations / محدودیت‌ها:** `Datetime` and `Time` remain standard Frappe controls, preserving timezone behavior. List/report result cells, calendar views, DateRange/Between filters, relative-date expressions, custom third-party widgets and website forms are not converted. Date input must use the full year/month/day format; Gregorian values passed to `set_value`, `frm.set_value` and API calls remain Gregorian. Invalid manual dates retain the previous model value and show a validation message. The picker supports Tab/Shift+Tab, Enter, Escape, and ArrowDown from the input; full arrow-key day-grid navigation and direct month/year selection are not implemented.

Print formats can opt in independently of the Desk setting:

```jinja
{{ jalali_date(doc.posting_date) }}
```

Python helpers are `iran_localization.modules.persian_calendar.utils.to_jalali` and `to_gregorian`. They share the existing `jdatetime` dependency used by official invoices. Browser conversion uses deterministic UTC day arithmetic with the same 33-year leap rule; it does not use browser locale conversion or remote scripts. Valid Jalali years are 1–9377, subject to the Gregorian year limit of 9999. No accounting dates or existing documents are rewritten.

Deploy with normal `bench --site erp.localhost migrate`, `bench build --app iran_localization`, and `bench --site erp.localhost clear-cache`. No Custom Field fixture or manual database change is required. See [calendar architecture and validation](docs/PERSIAN_CALENDAR.md) for checks and manual test steps.

# Iran Localization for ERPNext

افزونهٔ ماژولار بومی‌سازی ایران برای **ERPNext / Frappe 15**.

هدف پروژه این است که قابلیت‌های موردنیاز کسب‌وکارهای ایرانی را بدون تغییر مستقیم در هستهٔ ERPNext اضافه کند. تمام فیلدها، تنظیمات، سرویس‌ها و منطق اختصاصی داخل همین App نگهداری می‌شوند.

> نسخه فعلی: `0.1.0`  
> نسخه‌های آزمایش‌شده: Frappe `15.121.3` و ERPNext `15.121.6`

برای توضیح کامل کار با ماژول‌ها، [راهنمای فارسی](docs/USER_GUIDE_FA.md) را ببینید.

---

## امکانات

| ماژول | امکانات | کلید فعال‌سازی |
|---|---|---|
| اطلاعات ایران | شناسه ملی، کد اقتصادی، شماره ثبت و کد پستی شرکت/مشتری/تأمین‌کننده | همیشه در دسترس |
| اعتبارسنجی | تبدیل ارقام فارسی/عربی، کنترل قالب و کنترل اختیاری رقم کنترل | `enable_core_validation` |
| قیمت‌گذاری | بروزرسانی هزینهٔ BOM و قیمت فروش، BOM چندسطحی، شاخه‌های مشترک، تشخیص چرخه | `enable_pricing_automation` |
| صورتحساب رسمی | ذخیره مشخصات طرفین، چاپ فارسی RTL و تاریخ شمسی | `enable_official_invoice_module` |
| پیامک | صف و سابقه درخواست، Provider آزمایشی و کاوه‌نگار | `enable_sms` |
| مؤدیان | صف مستقل از حسابداری، Provider آزمایشی و HTTP gateway قابل تعویض | `enable_taxpayer_system` |
| فروشگاه/API | کاتالوگ منتخب، محاسبه قیمت/مالیات سمت سرور و سفارش Draft | `enable_commerce_api` |

ماژول‌های اختیاری در نصب جدید خاموش هستند. مقادیر Site-specific مانند Price List، شرکت، مشتری و Provider برای هر Site جداگانه تنظیم می‌شوند.

---

# نصب

## پیش‌نیازها

قبل از نصب:

- Frappe / ERPNext v15
- یک Bench فعال
- یک Site که ERPNext روی آن نصب شده باشد
- Git
- دسترسی ترمینال سرور یا Dev Container

نسخه‌ها را بررسی کنید:

```bash
bench version
```

---

## نصب مستقیم از GitHub

از پوشه Bench:

```bash
cd /path/to/frappe-bench
```

نسخه پایدار:

```bash
bench get-app https://github.com/halmasi/erpnext-Iran-Localization.git
```

نسخه توسعه:

```bash
bench get-app --branch develop https://github.com/halmasi/erpnext-Iran-Localization.git
```

سپس روی Site نصب کنید:

```bash
bench --site YOUR_SITE install-app iran_localization
```

مثال:

```bash
bench --site erp.localhost install-app iran_localization
```

بعد migration و build:

```bash
bench --site YOUR_SITE migrate
bench build --app iran_localization
```

بررسی نصب:

```bash
bench --site YOUR_SITE list-apps
```

باید `iran_localization` در خروجی دیده شود.

---

## نصب از مسیر محلی

اگر سورس App را روی سیستم دارید:

```bash
bench get-app /absolute/path/to/iran_localization
bench --site YOUR_SITE install-app iran_localization
bench --site YOUR_SITE migrate
bench build --app iran_localization
```

---

# تنظیم اولیه بعد از نصب

در ERPNext وارد Workspace یا صفحه زیر شوید:

```text
Iran Localization
```

سپس:

```text
Iran Localization Settings
```

را باز کنید.

پیشنهاد شروع:

```text
Core Validation        ON
Pricing Automation     OFF
Official Invoice       OFF
SMS                    OFF
Taxpayer System        OFF
Commerce API           OFF
```

هر ماژول را فقط بعد از تکمیل تنظیمات موردنیازش فعال کنید.

---

# ارتقا

قبل از ارتقا Backup بگیرید:

```bash
bench --site YOUR_SITE backup --with-files
```

سپس:

```bash
cd /path/to/frappe-bench/apps/iran_localization
git pull
cd ../..
```

وابستگی‌ها را بروزرسانی کنید:

```bash
./env/bin/python -m pip install -e apps/iran_localization
```

و سپس:

```bash
bench --site YOUR_SITE migrate
bench build --app iran_localization
bench --site YOUR_SITE clear-cache
```

---

# حذف افزونه

قبل از حذف Backup بگیرید.

```bash
bench --site YOUR_SITE uninstall-app iran_localization
```

بعد از uninstall، در صورت نیاز می‌توانید سورس App را نیز از Bench حذف کنید.

---

# تنظیمات و Fixtures

schema تنظیمات به‌صورت DocType استاندارد نگهداری می‌شود.

مقادیر Site-specific مانند:

- Price List
- شرکت
- مشتری
- کلید API
- تنظیمات Providerها

نباید داخل fixture عمومی پروژه قرار بگیرند.

`export-fixtures` فقط باید ساختارهای قابل‌انتقال App را صادر کند، نه تنظیمات واقعی یک شرکت.

---

# قیمت‌گذاری خودکار

برای فعال‌سازی:

1. Price List مواد اولیه را انتخاب کنید.
2. Price List فروش محصولات را انتخاب کنید.
3. درصد سربار را تعیین کنید.
4. درصد سود را تعیین کنید.
5. `Pricing Automation` را فعال کنید.

Price List خرید مواد اولیه و فروش محصولات باید متفاوت و فعال باشند.

فرمول:

```text
قیمت واحد = (هزینه کل BOM / مقدار خروجی BOM)
           × (1 + سربار / 100)
           × (1 + حاشیه سود / 100)
```

BOMهای Submit‌شده بروزرسانی می‌شوند و وابستگی‌های چندسطحی نیز propagate می‌شوند. چرخه با خطای مشخص متوقف می‌شود.

قیمت اختصاصی مشتری، تأمین‌کننده، Batch یا قیمت آینده بازنویسی نمی‌شود.

---

# صورتحساب فارسی

برای استفاده:

1. ماژول صورتحساب رسمی را فعال کنید.
2. در Sales Invoice گزینهٔ «صورتحساب رسمی ایران» را فعال کنید.
3. اطلاعات ثبتی طرفین را کامل کنید.

قالب:

```text
Iran Official Invoice
```

از مبالغ، مالیات و rounding خود ERPNext استفاده می‌کند.

> چاپ صورتحساب فارسی به‌معنی تأیید یا پذیرش آن در سامانه مؤدیان نیست.

---

# پیامک و سامانه مؤدیان

Provider موردنظر را از Settings انتخاب کنید.

`mock` فقط برای تست است و ارسال واقعی انجام نمی‌دهد.

برای کاوه‌نگار:

```text
sms_api_key
sms_sender
```

لازم است.

ماژول مؤدیان از عملیات عادی ERP جداست و خرابی یا خاموش بودن آن نباید مانع فروش، خرید، حسابداری یا صدور فاکتور عادی شود.

وضعیت‌های ممکن درخواست:

```text
Pending
Sent
Simulated
Unknown
Failed
```

`Sent` صرفاً به معنی پذیرش درخواست توسط Provider است و الزاماً پذیرش نهایی مالیاتی نیست.

---

# API فروشگاه

API برای Backend احراز هویت‌شده طراحی شده است. API Key را در Browser یا Frontend عمومی قرار ندهید.

Endpointهای فعلی:

| Method | مسیر `/api/method/` |
|---|---|
| GET | `iran_localization.modules.commerce.api.catalog` |
| POST | `iran_localization.modules.commerce.api.quote` |
| POST | `iran_localization.modules.commerce.api.create_order` |

نمونه درخواست:

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

قیمت و مالیات سمت ERPNext محاسبه می‌شوند.

---

# تست و توسعه

اجرای تست‌ها:

```bash
./env/bin/python apps/iran_localization/scripts/run_tests.py --site YOUR_TEST_SITE
```

Lint:

```bash
ruff check apps/iran_localization/iran_localization
```

Format check:

```bash
ruff format --check apps/iran_localization/iran_localization
```

تست‌ها شامل schema، تنظیمات، Validation، BOM مستقیم و چندسطحی، چرخه، Item Price، Permission، idempotency، SMS/Taxpayer mock و چاپ فارسی هستند.

---

# ساختار ماژولار

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

هر قابلیت باید تا حد امکان مستقل، قابل تست و قابل فعال/غیرفعال‌سازی باشد.

---

# اصول طراحی

- عدم تغییر مستقیم ERPNext Core
- قابلیت نصب روی پروژه‌های دیگر
- Site-specific بودن تنظیمات
- ماژولار بودن قابلیت‌ها
- اختیاری بودن مؤدیان
- مستقل بودن عملیات عادی ERP از Integrationهای بیرونی
- قابلیت اضافه‌کردن Providerهای جدید
- سازگاری با Upgradeهای آینده تا حد امکان

---

# وضعیت فعلی

نسخه:

```text
0.1.0
```

نسخه‌های آزمایش‌شده:

```text
Frappe 15.121.3
ERPNext 15.121.6
```

مواردی که قبل از Release پایدار باید بررسی شوند:

- نصب روی Site کاملاً جدید
- Restart واقعی Dev Container / Production
- نصب و ارتقا روی محیط تمیز
- تست Provider واقعی SMS
- تست Gateway واقعی مؤدیان
- Production deployment

---

# مشارکت

Issue و Pull Request برای رفع باگ، بهبود ترجمه، افزودن Provider، سازگاری ERPNext و توسعه قابلیت‌های بومی ایران خوش‌آمد است.

---

# منابع

- [Kavenegar REST API](https://kavenegar.github.io/kavenegar_en/)
- [Persian Tools — Legal ID validation](https://github.com/persian-tools/persian-tools/blob/master/src/modules/legalId/index.ts)
- [Iranian National ID validator](https://github.com/hamed-zeidabadi/iranian-national-id-validator)
- [jdatetime](https://pypi.org/project/jdatetime/)

---

# License

MIT

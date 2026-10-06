import frappe
from frappe.utils import flt


def update_product_prices_from_raw_material(doc, method=None):
    settings = frappe.get_single("Iran Localization Settings")

    raw_material_price_list = settings.raw_material_price_list
    selling_price_list = settings.selling_price_list

    if not raw_material_price_list or not selling_price_list:
        return

    # فقط تغییر قیمت مواد اولیه باید این زنجیره را شروع کند
    if doc.price_list != raw_material_price_list:
        return

    visited_boms = set()

    _update_dependent_boms_and_prices(
        item_code=doc.item_code,
        settings=settings,
        visited_boms=visited_boms,
    )


def _update_dependent_boms_and_prices(item_code, settings, visited_boms):
    """
    تمام BOMهایی که item_code را مصرف می‌کنند پیدا می‌کند،
    هزینه آنها را به‌روزرسانی می‌کند و سپس همین روند را
    برای محصول خروجی آن BOM به صورت recursive ادامه می‌دهد.
    """

    bom_items = frappe.get_all(
        "BOM Item",
        filters={"item_code": item_code},
        fields=["parent"],
        distinct=True,
    )

    for row in bom_items:
        bom_name = row.parent

        # جلوگیری از loop
        if bom_name in visited_boms:
            continue

        visited_boms.add(bom_name)

        bom = frappe.get_doc("BOM", bom_name)

        # فقط BOMهای Submit شده
        if bom.docstatus != 1:
            continue

        # هزینه BOM را مجدداً محاسبه کن
        bom.update_cost()
        bom.reload()

        finished_item = bom.item
        base_cost = flt(bom.total_cost)

        _update_selling_price(
            item_code=finished_item,
            base_cost=base_cost,
            settings=settings,
        )

        # این محصول ممکن است خودش ماده اولیه BOM دیگری باشد
        _update_dependent_boms_and_prices(
            item_code=finished_item,
            settings=settings,
            visited_boms=visited_boms,
        )


def _update_selling_price(item_code, base_cost, settings):
    selling_price_list = settings.selling_price_list

    overhead_percent = flt(settings.manufacturing_overhead_percent)
    profit_percent = flt(settings.profit_markup_percent)

    price = flt(base_cost)

    price *= 1 + (overhead_percent / 100)
    price *= 1 + (profit_percent / 100)

    existing_price = frappe.db.exists(
        "Item Price",
        {
            "item_code": item_code,
            "price_list": selling_price_list,
        },
    )

    if existing_price:
        item_price = frappe.get_doc("Item Price", existing_price)
        item_price.price_list_rate = price
        item_price.save(ignore_permissions=True)

    else:
        frappe.get_doc(
            {
                "doctype": "Item Price",
                "item_code": item_code,
                "price_list": selling_price_list,
                "price_list_rate": price,
            }
        ).insert(ignore_permissions=True)

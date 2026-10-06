import frappe
from frappe.utils import flt


def update_product_prices_from_raw_material(doc, method=None):
    settings = frappe.get_single("Iran Localization Settings")

    raw_material_price_list = settings.raw_material_price_list
    selling_price_list = settings.selling_price_list

    if not raw_material_price_list or not selling_price_list:
        return

    # فقط وقتی قیمت مربوط به Price List مواد اولیه باشد
    if doc.price_list != raw_material_price_list:
        return

    raw_item_code = doc.item_code

    # BOMهایی که این ماده اولیه داخلشان استفاده شده
    bom_items = frappe.get_all(
        "BOM Item",
        filters={"item_code": raw_item_code},
        fields=["parent"],
        distinct=True,
    )

    for row in bom_items:
        bom_name = row.parent

        bom = frappe.get_doc("BOM", bom_name)

        if bom.docstatus != 1:
            continue

        # Recalculate and persist BOM cost
        bom.update_cost()

        # Reload so we read the persisted, latest values
        bom.reload()

        finished_item = bom.item
        base_cost = flt(bom.total_cost)

        overhead_percent = flt(settings.manufacturing_overhead_percent)
        profit_percent = flt(settings.profit_markup_percent)

        price = base_cost

        price *= 1 + (overhead_percent / 100)
        price *= 1 + (profit_percent / 100)

        existing_price = frappe.db.exists(
            "Item Price",
            {
                "item_code": finished_item,
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
                    "item_code": finished_item,
                    "price_list": selling_price_list,
                    "price_list_rate": price,
                }
            ).insert(ignore_permissions=True)

    frappe.db.commit()

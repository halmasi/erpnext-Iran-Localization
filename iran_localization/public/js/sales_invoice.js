frappe.ui.form.on("Sales Invoice", {
    items_add(frm, cdt, cdn) {
        fetch_item_price(frm, cdt, cdn);
    },
    item_code(frm, cdt, cdn) {
        fetch_item_price(frm, cdt, cdn);
    },
    selling_price_list(frm) {
        (frm.doc.items || []).forEach((row) => fetch_item_price(frm, row.doctype, row.name));
    },
    refresh(frm) {
        frappe.call({
            method: "iran_localization.modules.official_invoice.service.module_status",
            callback({ message: status }) {
                if (!status) return;
                frm.toggle_display("iran_invoice_section", status.enable_official_invoice_module);
                frm.toggle_display("iran_official_invoice", status.enable_official_invoice_module);
                if (status.enable_official_invoice_module && !frm.is_new()) {
                    frm.add_custom_button(__("Persian Invoice"), () => {
                        frappe.route_options = { print_format: "Iran Official Invoice" };
                        frappe.set_route("print", "Sales Invoice", frm.doc.name);
                    });
                }
                if (status.enable_taxpayer_system && frm.doc.docstatus === 1 && frappe.user.has_role("System Manager")) {
                    frm.add_custom_button(__("Queue Taxpayer Invoice"), () => {
                        frappe.call({
                            method: "iran_localization.modules.taxpayer.service.queue_invoice",
                            args: { name: frm.doc.name },
                            callback({ message }) {
                                if (message) frappe.set_route("Form", "Iran Integration Request", message.name);
                            },
                        });
                    });
                }
            },
        });
    },
});

frappe.ui.form.on("Sales Invoice Item", {
    item_code(frm, cdt, cdn) {
        frappe.after_ajax(() => fetch_item_price(frm, cdt, cdn));
    },
    uom(frm, cdt, cdn) {
        frappe.after_ajax(() => fetch_item_price(frm, cdt, cdn));
    },
});

function fetch_item_price(frm, cdt, cdn) {
    const row = locals[cdt][cdn];
    if (!row || !row.item_code || flt(row.rate)) return;
    frappe.call({
        method: "iran_localization.modules.pricing.service.get_sales_item_price",
        args: { item_code: row.item_code, price_list: frm.doc.selling_price_list, uom: row.uom },
        callback(r) {
            if (r.message == null || !frm.doc.items.some((item) => item.name === cdn)) return;
            frappe.model.set_value(cdt, cdn, "price_list_rate", r.message);
            frappe.model.set_value(cdt, cdn, "rate", r.message);
        },
    });
}

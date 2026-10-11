frappe.ui.form.on("Sales Invoice", {
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

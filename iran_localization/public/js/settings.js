frappe.ui.form.on("Iran Localization Settings", {
    after_save(frm) {
        if (frm._persian_language !== Boolean(frm.doc.enable_persian_language) ||
            frm._persian_calendar !== Boolean(frm.doc.enable_persian_calendar)) {
            window.location.reload();
        }
    },
    onload(frm) {
        frm._persian_language = Boolean(frm.doc.enable_persian_language);
        frm._persian_calendar = Boolean(frm.doc.enable_persian_calendar);
    },
    refresh(frm) {
        frm.set_query("raw_material_price_list", () => ({ filters: { buying: 1, enabled: 1 } }));
        ["selling_price_list", "commerce_price_list"].forEach((field) => {
            frm.set_query(field, () => ({ filters: { selling: 1, enabled: 1 } }));
        });
        frm.add_custom_button(__("Installed Providers"), () => {
            frappe.call({
                method: "iran_localization.modules.integrations.registry.list_providers",
                callback({ message }) {
                    const rows = Object.entries(message || {}).map(([kind, entries]) =>
                        `<p><b>${frappe.utils.escape_html(kind)}</b>: ${entries.map((entry) =>
                            `${frappe.utils.escape_html(entry.key)} — ${frappe.utils.escape_html(entry.label)}`
                        ).join("<br>")}</p>`
                    );
                    frappe.msgprint({ title: __("Installed Providers"), message: rows.join("") });
                },
            });
        });
        frm.add_custom_button(__("Integration Requests"), () => frappe.set_route("List", "Iran Integration Request"));
        if (frm.doc.enable_sms) {
            frm.add_custom_button(__("Queue SMS"), () => {
                frappe.prompt([
                    { fieldname: "recipient", fieldtype: "Data", label: __("Mobile number"), reqd: 1 },
                    { fieldname: "message", fieldtype: "Small Text", label: __("Message"), reqd: 1 },
                ], (values) => {
                    frappe.call({
                        method: "iran_localization.modules.sms.service.queue_sms",
                        args: { ...values, request_id: crypto.randomUUID() },
                        callback({ message }) {
                            if (message) frappe.set_route("Form", "Iran Integration Request", message.name);
                        },
                    });
                }, __("Queue SMS"));
            });
        }
    },
});

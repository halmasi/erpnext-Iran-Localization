frappe.ui.form.on("Iran Integration Request", {
    refresh(frm) {
        if (["Pending", "Failed"].includes(frm.doc.status) && !frm.is_new() && frappe.user.has_role("System Manager")) {
            frm.add_custom_button(__("Refresh Provider"), () => frappe.confirm(
                __("Refresh this unsent request using the current provider settings?"),
                () => frappe.call({
                    method: "iran_localization.modules.integrations.service.refresh_provider",
                    args: { name: frm.doc.name },
                    callback() { frm.reload_doc(); },
                })
            ));
        }
        if (frm.doc.status === "Failed" && frappe.user.has_role("System Manager")) {
            frm.add_custom_button(__("Retry Request"), () => frappe.call({
                method: "iran_localization.modules.integrations.service.retry_request",
                args: { name: frm.doc.name },
                callback() { frm.reload_doc(); },
            }));
        }
        if (["Unknown", "Processing"].includes(frm.doc.status) && frappe.user.has_role("System Manager")) {
            frm.add_custom_button(__("Reconcile Delivery"), () => frappe.prompt([
                { fieldname: "accepted", fieldtype: "Check", label: __("Provider confirmed acceptance") },
                { fieldname: "provider_reference", fieldtype: "Data", label: __("Provider reference") },
            ], (values) => frappe.call({
                method: "iran_localization.modules.integrations.service.reconcile",
                args: { name: frm.doc.name, ...values },
                callback() { frm.reload_doc(); },
            }), __("Reconcile Delivery")));
        }
        if (frm.doc.status === "Pending" && !frm.is_new() && frappe.user.has_role("System Manager")) {
            frm.add_custom_button(__("Send Request"), () => {
                frappe.confirm(__("Send this request using its selected provider?"), () => {
                    frappe.call({
                        method: "iran_localization.modules.integrations.service.dispatch",
                        args: { name: frm.doc.name },
                        callback() { frm.reload_doc(); },
                    });
                });
            });
        }
    },
});

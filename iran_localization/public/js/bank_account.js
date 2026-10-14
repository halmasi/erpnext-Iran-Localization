frappe.ui.form.on("Bank Account", {
    async refresh(frm) {
        const { message: options } = await frappe.call({
            method: "iran_localization.modules.banking.options",
        });
        if (!options) return;
        frm.toggle_display("iran_card_number", options.enable_iran_card_number);
        frm.toggle_display("iran_sheba", options.enable_iran_sheba);
        ["iban", "iran_sheba", "iran_card_number", "bank_account_no"].forEach((field) => {
            const input = frm.fields_dict[field]?.$input;
            if (input) input.attr("dir", "ltr").css({ direction: "ltr", "text-align": "left", "unicode-bidi": "isolate" });
        });
        frm.set_query("bank", () => ({
            filters: options.enable_iran_bank_list ? { iran_bank: 1 } : {},
        }));
        if (options.enable_iran_bank_list && frappe.model.can_create("Bank")) {
            frm.add_custom_button("افزودن بانک ایرانی", () => {
                frappe.new_doc("Bank", { iran_bank: 1 });
            });
        }
    },
});

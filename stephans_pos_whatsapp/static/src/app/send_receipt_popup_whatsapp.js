import { patch } from "@web/core/utils/patch";
import { SendReceiptPopup } from "@point_of_sale/app/components/popups/send_receipt_popup/send_receipt_popup";

// Adds a WhatsApp button (official logo) next to the phone field of the Send Receipt popup.
patch(SendReceiptPopup.prototype, {
    showPhoneInput() {
        return super.showPhoneInput() || Boolean(this.pos.config.whatsapp_receipt);
    },
    // Odoo's isValidPhone only accepts "+<country>..."; cashiers type local Tanzanian numbers
    // (0769 324 445). Accept the formats the server normalises (normalize_whatsapp_phone).
    get isValidWhatsAppPhone() {
        const digits = (this.state.phone || "").replace(/[\s.\-()]/g, "");
        return (
            /^\+\d{8,18}$/.test(digits) ||
            /^0[67]\d{8}$/.test(digits) ||
            /^[67]\d{8}$/.test(digits) ||
            /^(00)?\d{11,15}$/.test(digits)
        );
    },
    actionSendReceiptOnWhatsApp() {
        this.sendReceipt.call({
            action: "action_send_whatsapp_receipt",
            destination: this.state.phone,
            name: "WhatsApp",
        });
    },
    get sendList() {
        const list = super.sendList;
        if (this.pos.config.whatsapp_receipt) {
            list.find((item) => item.model === "phone").buttons.push({
                click: () => this.actionSendReceiptOnWhatsApp(),
                status: this.sendReceipt.lastArgs?.[0]?.name == "WhatsApp" && this.sendReceipt.status,
                icon: "chat",
                image: "/stephans_pos_whatsapp/static/src/img/whatsapp.png",
                btnClass: "o_whatsapp_receipt_btn",
                title: "Send on WhatsApp",
                disabled: () => !this.isValidWhatsAppPhone,
            });
        }
        return list;
    },
});

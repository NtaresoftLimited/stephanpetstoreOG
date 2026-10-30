/** @odoo-module */

import { _t } from "@web/core/l10n/translation";
import { register_payment_method } from "@point_of_sale/app/store/pos_store";
import { PaymentInterface } from "@point_of_sale/app/payment/payment_interface";
import { uuidv4 } from "@point_of_sale/utils";
import { AlertDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { makeAwaitable, ask } from "@point_of_sale/app/store/make_awaitable_dialog";

export class PaymentSelcom extends PaymentInterface {


   setup() {
        super.setup(...arguments);
        this.paymentLineResolvers = {};
    }

    send_payment_request(uuid) {
        super.send_payment_request(uuid);
        return this._selcom_pay(uuid);
    }

    /**
     * @override
     *
     * At the moment, POS payments are no cancellable from the Selcom API.
     * It can be only cancelled from the terminal itself. If you cancel the
     * transaction from the terminal, we get notification and `handleSelcomStatusResponse`
     * will handle cancellation. For force cancellation we show popup then cancel.
     */

      async send_payment_cancel(order, uuid) {
        super.send_payment_cancel(order, uuid);
        const paymentLine = this.pending_selcom_line();
        paymentLine.set_payment_status('retry');
        this.env.services.orm.silent.call('selcom.pos.terminal.payments', 'update_status',[[ ],order.pos_reference.replace(/Order/g, "").replace(/\s+/g, "").replace(/-/g, "")])
        return true;
    }


    set_most_recent_Selcom_uid(id) {
        this.most_recent_Selcom_uid = id;
    }

    pending_selcom_line() {
        return this.pos.getPendingPaymentLine("selcom");
    }

    _handle_odoo_connection_failure(data = {}) {
        var line = this.pending_selcom_line();
        if (line) {
            line.set_payment_status("retry");
        }
        this._show_error(
            _t("Could not connect to the Odoo server, please check your internet connection and try again.")
        );
        return Promise.reject(data);
    }

    _submit_selcom_payment(data) {
        return this.env.services.orm.silent
            .call('pos.payment.method', 'selcom_payment_request', [
                [this.payment_method_id.id],
                data
            ]).catch(this._handle_odoo_connection_failure.bind(this));
    }

    _selcom_pay_data() {
        var order = this.pos.get_order();
        var line = order.get_selected_paymentline();
        this.most_recent_selcom_uid = uuidv4();
        return {
            'selcom_uid': this.most_recent_selcom_uid,
            'description': order.name,
            'order_id': order.pos_reference.replace(/Order/g, "").replace(/\s+/g, "").replace(/-/g, ""),
            'currency': this.pos.currency.name,
            'company_id':this.pos.company.id,
            'currency_id':this.pos.currency.id,
            'amount': Number(line.amount),
            'session_id': order.session_id.id,
            'payment_method_id': this.payment_method_id.id
        }
    }

    _selcom_pay(uuid) {
        var order = this.pos.get_order();
        if (order.get_selected_paymentline().amount < 0) {
            this._show_error(_t("Cannot process transactions with negative amount."));
            return Promise.resolve();
        }
        var data = this._selcom_pay_data();
        var line = order.payment_ids.find((paymentLine) => paymentLine.uuid === uuid);
        line.setTerminalServiceId(this.most_recent_service_id);
        return this._submit_selcom_payment(data).then((data) => {
            return this._selcom_handle_response(data);
        });
    }

    async handleSelcomStatusResponse() {
        const line = this.pending_selcom_line();
        const paymentStatus = await this.env.services.orm.silent
            .call('selcom.pos.terminal.payments', 'get_selcom_payment_status', [
                []], {
                selcom_uid: this.most_recent_selcom_uid
            })
        if (!paymentStatus) {
            this._handle_odoo_connection_failure();
            return;
        }
        const resolver = this.paymentLineResolvers?.[line.uuid];
        if (paymentStatus.result == 'SUCCESS') {
            this._resolvePaymentStatus(true);
        } else if (paymentStatus.result != 'SUCCESS') {
            this._resolvePaymentStatus(false);
        }
    }
    _resolvePaymentStatus(state) {

        const line = this.pending_selcom_line();
        const resolver = this.paymentLineResolvers?.[line.uuid];
        if (resolver) {
            resolver(state);
        } else {
            line.handle_payment_response(state);
        }
    }

    /**
     * This method handles the response that comes from selcom
     * when we first make a request to pay.
     */
      _selcom_handle_response(response) {
        var line = this.pending_selcom_line();
        if (response != 'undefined'){
                if (response?.result != 'SUCCESS') {
                this._show_error(response.message);
                line.set_payment_status('retry');
                return Promise.resolve();
            }
            if (response.id) {
                line.transaction_id = response.id;
            }
            return this.waitForPaymentConfirmation();
        }else{
            return this.waitForPaymentConfirmation();
        }
    }

    waitForPaymentConfirmation() {
        return new Promise((resolve) => {
            this.paymentLineResolvers[this.pending_selcom_line()] = resolve;
        });
    }


    _show_error(msg, title) {
        if (!title) {
            title = _t("Selcom Error");
        }
       this.env.services.dialog.add(AlertDialog, {
                   title: title,
                    body: msg,
        });
    }
}


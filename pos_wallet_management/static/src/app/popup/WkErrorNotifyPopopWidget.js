/** @odoo-module */

/* Copyright (c) 2016-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>) */
/* See LICENSE file for full copyright and licensing details. */
/* License URL : <https://store.webkul.com/license.html/> */

import { Component, onMounted } from "@odoo/owl";
import { Dialog } from "@web/core/dialog/dialog";
import { usePos } from "@point_of_sale/app/store/pos_hook";

export class WkErrorNotifyPopopWidget extends Component {

    static template = "pos_wallet_management.WkErrorNotifyPopopWidget";
    static components = { Dialog };
    static defaultProps = {  
        title: 'Confirm ?',
        body: '',
        confirmText:'Ok',
    };

    setup() {
        super.setup();
        this.pos = usePos();
        onMounted(this.Mounte);
    }

    Mounte() {
        setTimeout(function () {
            $('.move').addClass('complete');
        }, 500)
    }

    cancel(){
        this.props.close();
    }

    _callRechargeWallet(){
        this.props.close();
        this.pos.openWalletRecharge()
    }

    confirm(){
        if(this.props.confirm){
            this.props.close()
            this.props.confirm();
        }
    }
}

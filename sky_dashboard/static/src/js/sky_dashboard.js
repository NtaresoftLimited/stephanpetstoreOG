/** @odoo-module **/

import { Component, onWillStart, useState } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { user } from "@web/core/user";

export class SkyDashboard extends Component {
    static template = "sky_dashboard.SkyDashboard";

    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.user = user;
        this.state = useState({ loading: true, data: null, canAccessDailyStock: false });

        onWillStart(async () => {
            let canAccessDailyStock = false;
            try {
                canAccessDailyStock = await user.hasGroup("sky_dashboard.group_sky_stock_cashier");
            } catch (e) {
                console.warn("Could not check group sky_dashboard.group_sky_stock_cashier:", e);
            }
            await this.loadDashboard();
            this.state.canAccessDailyStock = canAccessDailyStock;
        });
    }

    async loadDashboard() {
        this.state.loading = true;
        this.state.data = await this.orm.call("sale.order", "get_sky_dashboard_data", []);
        this.state.loading = false;
    }

    formatMoney(value) {
        return `${this.state.data.currency} ${new Intl.NumberFormat().format(value || 0)}`;
    }

    get donutStyle() {
        const states = this.state.data.states;
        const total = Object.values(states).reduce((sum, value) => sum + value, 0) || 1;
        const quotation = (states.quotation / total) * 100;
        const confirmed = quotation + (states.confirmed / total) * 100;
        const done = confirmed + (states.done / total) * 100;
        return `background: conic-gradient(#C77E35 0 ${quotation}%, #4E2A15 ${quotation}% ${confirmed}%, #D8B58E ${confirmed}% ${done}%, #E8E0D8 ${done}% 100%)`;
    }

    openOrders(domain = []) {
        this.action.doAction({
            type: "ir.actions.act_window",
            name: "Sales Orders",
            res_model: "sale.order",
            views: [[false, "list"], [false, "form"]],
            domain,
        });
    }

    openOrder(orderId) {
        this.action.doAction({
            type: "ir.actions.act_window",
            name: "Sales Order",
            res_model: "sale.order",
            res_id: orderId,
            views: [[false, "form"]],
        });
    }

    openCustomers() {
        this.action.doAction({
            type: "ir.actions.act_window",
            name: "Customers",
            res_model: "res.partner",
            views: [[false, "kanban"], [false, "list"], [false, "form"]],
            domain: [["customer_rank", ">", 0]],
        });
    }

    openProducts() {
        this.action.doAction({
            type: "ir.actions.act_window",
            name: "Products",
            res_model: "product.template",
            views: [[false, "kanban"], [false, "list"], [false, "form"]],
            domain: [["sale_ok", "=", true]],
        });
    }

    openDailyStock() {
        this.action.doAction("sky_dashboard.action_sky_daily_stock");
    }
}

registry.category("actions").add("sky.dashboard", SkyDashboard);

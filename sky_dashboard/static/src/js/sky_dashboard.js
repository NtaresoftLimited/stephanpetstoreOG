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
        const now = new Date();
        const monday = new Date(now);
        monday.setDate(now.getDate() - ((now.getDay() + 6) % 7));
        const sunday = new Date(monday);
        sunday.setDate(monday.getDate() + 6);
        const isoDate = (date) => date.toISOString().slice(0, 10);
        this.state = useState({
            loading: true, data: null, canAccessDailyStock: false, isAdmin: false,
            dateStart: isoDate(monday), dateEnd: isoDate(sunday), configId: 0,
        });

        onWillStart(async () => {
            let canAccessDailyStock = false;
            let isAdmin = false;
            try {
                canAccessDailyStock = await user.hasGroup("sky_dashboard.group_sky_stock_cashier");
            } catch (e) {
                console.warn("Could not check group sky_dashboard.group_sky_stock_cashier:", e);
            }
            try {
                isAdmin = await user.hasGroup("base.group_system");
            } catch (e) {
                console.warn("Could not check group base.group_system:", e);
            }
            await this.loadDashboard();
            this.state.canAccessDailyStock = canAccessDailyStock;
            this.state.isAdmin = isAdmin;
        });
    }

    async loadDashboard() {
        this.state.loading = true;
        this.state.data = await this.orm.call("sale.order", "get_sky_dashboard_data", [], {
            options: {
                date_start: this.state.dateStart,
                date_end: this.state.dateEnd,
                config_id: this.state.configId,
            },
        });
        this.state.dateStart = this.state.data.weekly.date_start;
        this.state.dateEnd = this.state.data.weekly.date_end;
        this.state.loading = false;
    }

    onDateStart(event) { this.state.dateStart = event.target.value; }
    onDateEnd(event) { this.state.dateEnd = event.target.value; }
    onConfigChange(event) { this.state.configId = Number(event.target.value || 0); }

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

    get weeklyFinanceDonutStyle() {
        const sales = Math.max(this.state.data.weekly.net_sales || 0, 0);
        const expenses = Math.max(this.state.data.weekly.expenses || 0, 0);
        const total = sales + expenses;
        if (!total) return "background: #eee8e1";
        const salesShare = (sales / total) * 100;
        return `background: conic-gradient(#4E2A15 0 ${salesShare}%, #C77E35 ${salesShare}% 100%)`;
    }

    get paymentDonutStyle() {
        const colors = ["#4E2A15", "#C77E35", "#D8B58E", "#7E9B76", "#B95C3F", "#8A8179"];
        const values = this.state.data.weekly.payments.map((payment) => Math.max(payment.amount || 0, 0));
        const total = values.reduce((sum, value) => sum + value, 0);
        if (!total) return "background: #eee8e1";
        let cursor = 0;
        const segments = values.map((value, index) => {
            const start = cursor;
            cursor += (value / total) * 100;
            return `${colors[index % colors.length]} ${start}% ${cursor}%`;
        });
        return `background: conic-gradient(${segments.join(", ")})`;
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

    openReplenishments() {
        this.action.doAction("grooming.action_grooming_stock_request");
    }

    openPosOrders(configId = 0) {
        const domain = [
            ["date_order", ">=", `${this.state.dateStart} 00:00:00`],
            ["date_order", "<=", `${this.state.dateEnd} 23:59:59`],
            ["state", "in", ["paid", "done", "invoiced"]],
        ];
        if (configId) domain.push(["config_id", "=", configId]);
        this.action.doAction({
            type: "ir.actions.act_window", name: "Point of Sale Orders", res_model: "pos.order",
            views: [[false, "list"], [false, "form"]], domain,
        });
    }

    openExpenses() {
        const domain = [
            ["date", ">=", this.state.dateStart], ["date", "<=", this.state.dateEnd],
            ["state", "in", ["approved", "paid"]],
        ];
        if (this.state.configId) domain.push(["pos_config_id", "=", this.state.configId]);
        this.action.doAction({
            type: "ir.actions.act_window", name: "Store Expenses", res_model: "pos.store.expense",
            views: [[false, "list"], [false, "form"]], domain,
        });
    }
}

registry.category("actions").add("sky.dashboard", SkyDashboard);

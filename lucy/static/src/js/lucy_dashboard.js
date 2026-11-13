/** @odoo-module **/

import { Component, onWillStart, proxy, useProps } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { standardActionServiceProps } from "@web/webclient/actions/action_plugin";

export class LucyDashboard extends Component {
    static template = "lucy.LucyDashboard";
    props = useProps({
        ...standardActionServiceProps,
    });

    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        const today = new Date();
        const start = new Date(today);
        start.setDate(today.getDate() - 6);
        const isoDate = (date) => date.toISOString().slice(0, 10);
        const action = this.props?.action || this.__owl__?.props?.action;
        const defaultTab = action?.context?.default_tab || action?.params?.default_tab || "overview";

        this.state = proxy({
            loading: true,
            data: null,
            dateStart: isoDate(start),
            dateEnd: isoDate(today),
            activeTab: defaultTab,
            activeCatalogKey: "dogs",
        });
        onWillStart(() => this.load());
    }

    async load() {
        this.state.loading = true;
        try {
            this.state.data = await this.orm.call("lucy.dashboard", "get_dashboard_data", [], {
                options: {
                    date_start: this.state.dateStart,
                    date_end: this.state.dateEnd,
                },
            });
            this.state.dateStart = this.state.data.date_start;
            this.state.dateEnd = this.state.data.date_end;
        } finally {
            this.state.loading = false;
        }
    }

    onDateStart(event) { this.state.dateStart = event.target.value; }
    onDateEnd(event) { this.state.dateEnd = event.target.value; }
    setActiveTab(tab) { this.state.activeTab = tab; }
    setCatalogCategory(key) { this.state.activeCatalogKey = key; }

    get todayDayNumber() {
        return new Date().getDate().toString().padStart(2, "0");
    }

    get todayFormattedDate() {
        return new Intl.DateTimeFormat(undefined, {
            weekday: "long",
            month: "long",
            year: "numeric",
        }).format(new Date());
    }

    money(value) {
        return `${this.state.data?.currency || "TZS"} ${new Intl.NumberFormat().format(Math.round(value || 0))}`;
    }

    donutStyle(segments) {
        const visible = (segments || []).filter((segment) => Number(segment.value) > 0);
        const total = visible.reduce((sum, segment) => sum + Number(segment.value || 0), 0);
        if (!total) return "background: conic-gradient(#ece8e3 0 100%);";
        let cursor = 0;
        const stops = visible.map((segment) => {
            const start = cursor;
            cursor += (Number(segment.value) / total) * 100;
            return `${segment.color} ${start.toFixed(2)}% ${cursor.toFixed(2)}%`;
        });
        return `background: conic-gradient(${stops.join(", ")});`;
    }

    chartHeight(value, rows, field) {
        const maximum = Math.max(...(rows || []).map((row) => Number(row[field] || 0)), 0);
        if (!maximum || !value) return "height: 3px;";
        return `height: ${Math.min(100, Math.max(5, (Number(value) / maximum) * 100)).toFixed(1)}%;`;
    }

    get revenueSegments() {
        return this.state.data?.overview?.channels || [];
    }

    get groomingSegments() {
        const grooming = this.state.data?.grooming || {};
        return [
            { name: "Pending", value: grooming.pending || 0, color: "#d5a252" },
            { name: "Confirmed", value: grooming.confirmed || 0, color: "#7f9d72" },
            { name: "In progress", value: grooming.in_progress || 0, color: "#4e2a15" },
            { name: "Completed", value: grooming.completed || 0, color: "#a9bea0" },
            { name: "Cancelled", value: grooming.cancelled || 0, color: "#c77762" },
        ];
    }

    get paymentSegments() {
        const colors = ["#4e2a15", "#c77e35", "#8da17e", "#9a8f86", "#d6c3ad"];
        return (this.state.data?.sky?.weekly?.payments || []).map((payment, index) => ({
            name: payment.name,
            value: payment.amount,
            color: colors[index % colors.length],
        }));
    }

    get stockSegments() {
        const inventory = this.state.data?.inventory || {};
        return [
            { name: "Healthy", value: inventory.healthy_stock || 0, color: "#8da17e" },
            { name: "Low stock", value: inventory.low_only || 0, color: "#d5a252" },
            { name: "Out of stock", value: inventory.out_of_stock || 0, color: "#c77762" },
        ];
    }

    get activeCatalog() {
        const groups = this.state.data?.catalog || [];
        return groups.find((group) => group.key === this.state.activeCatalogKey) || groups[0] || null;
    }

    get catalogStockSegments() {
        const catalog = this.activeCatalog || {};
        return [
            { name: "Healthy", value: catalog.healthy || 0, color: "#8da17e" },
            { name: "Low stock", value: catalog.low_stock || 0, color: "#d5a252" },
            { name: "Out of stock", value: catalog.out_of_stock || 0, color: "#c77762" },
        ];
    }

    get catalogRevenueSegments() {
        const catalog = this.activeCatalog || {};
        return [
            { name: "Point of Sale", value: catalog.pos_revenue || 0, color: "#4e2a15" },
            { name: "Website", value: catalog.website_revenue || 0, color: "#c77e35" },
        ];
    }

    openCatalogProducts(kind = "all") {
        const catalog = this.activeCatalog;
        if (!catalog) return;
        const domain = [
            ["active", "=", true],
            ["sale_ok", "=", true],
            ["categ_id", "in", catalog.category_ids || []],
        ];
        if (kind === "missing_images") domain.push(["image_128", "=", false]);
        if (kind === "zero_price") domain.push(["list_price", "<=", 0]);
        if (kind === "missing_description") {
            domain.push(["description_sale", "=", false], ["description", "=", false]);
        }
        if (kind === "out_of_stock") domain.push(["qty_available", "<=", 0]);
        this.action.doAction({
            type: "ir.actions.act_window",
            name: `${catalog.name} Products`,
            res_model: "product.template",
            views: [[false, "list"], [false, "kanban"], [false, "form"]],
            domain,
        });
    }

    openAction(action) {
        this.action.doAction(action);
    }

    openWebsiteOrders(kind = "all") {
        const utcStart = this.state.data?.utc_start;
        const utcEnd = this.state.data?.utc_end;
        const period = [];
        if (utcStart && utcEnd) {
            period.push(["date_order", ">=", utcStart], ["date_order", "<", utcEnd]);
        }
        const domains = {
            all: [
                ...period,
                "|",
                ["website_id", "!=", false],
                ["lucy_order_channel", "=", "nextjs"],
            ],
            draft: [
                ...period,
                ["state", "in", ["draft", "sent"]],
                "|",
                ["website_id", "!=", false],
                ["lucy_order_channel", "=", "nextjs"],
            ],
            confirmed: [
                ...period,
                ["state", "in", ["sale", "done"]],
                "|",
                ["website_id", "!=", false],
                ["lucy_order_channel", "=", "nextjs"],
            ],
            payment_pending: [
                ...period,
                ["state", "in", ["sale", "done"]],
                ["invoice_ids.payment_state", "not in", ["in_payment", "paid"]],
                "|",
                ["website_id", "!=", false],
                ["lucy_order_channel", "=", "nextjs"],
            ],
            paid: [
                ...period,
                ["invoice_ids.state", "=", "posted"],
                ["invoice_ids.payment_state", "in", ["in_payment", "paid"]],
                "|",
                ["website_id", "!=", false],
                ["lucy_order_channel", "=", "nextjs"],
            ],
            processing: [
                ...period,
                ["state", "in", ["sale", "done"]],
                ["picking_ids.state", "not in", ["done", "cancel"]],
                "|",
                ["website_id", "!=", false],
                ["lucy_order_channel", "=", "nextjs"],
            ],
            delivered: [
                ...period,
                ["picking_ids.state", "=", "done"],
                "|",
                ["website_id", "!=", false],
                ["lucy_order_channel", "=", "nextjs"],
            ],
            cancelled: [
                ...period,
                ["state", "=", "cancel"],
                "|",
                ["website_id", "!=", false],
                ["lucy_order_channel", "=", "nextjs"],
            ],
        };
        this.action.doAction({
            type: "ir.actions.act_window",
            name: "Website Orders",
            res_model: "sale.order",
            views: [[false, "list"], [false, "kanban"], [false, "form"]],
            domain: domains[kind] || domains.all,
        });
    }

    openGrooming(state = "all") {
        const domain = [["booking_source", "in", ["odoo_website", "nextjs", "portal"]]];
        if (this.state.data?.utc_start && this.state.data?.utc_end) {
            domain.unshift(
                ["appointment_date", ">=", this.state.data.utc_start],
                ["appointment_date", "<", this.state.data.utc_end]
            );
        }
        if (state === "in_progress") {
            domain.push(["state", "in", ["checked_in", "in_progress", "halfway"]]);
        } else if (state !== "all") {
            domain.push(["state", "=", state]);
        }
        this.action.doAction({
            type: "ir.actions.act_window",
            name: "Website Grooming Bookings",
            res_model: "grooming.appointment",
            views: [[false, "list"], [false, "kanban"], [false, "calendar"], [false, "form"]],
            domain,
        });
    }

    openPosOrders() {
        const domain = [["state", "in", ["paid", "done", "invoiced"]]];
        if (this.state.data?.utc_start && this.state.data?.utc_end) {
            domain.unshift(
                ["date_order", ">=", this.state.data.utc_start],
                ["date_order", "<", this.state.data.utc_end]
            );
        }
        this.action.doAction({
            type: "ir.actions.act_window",
            name: "Point of Sale Orders",
            res_model: "pos.order",
            views: [[false, "list"], [false, "form"], [false, "pivot"], [false, "graph"]],
            domain,
        });
    }

    openRecord(model, id, name) {
        this.action.doAction({
            type: "ir.actions.act_window",
            name,
            res_model: model,
            res_id: id,
            views: [[false, "form"]],
        });
    }
}

registry.category("actions").add("lucy.dashboard", LucyDashboard);

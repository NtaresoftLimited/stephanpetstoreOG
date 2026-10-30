/** @odoo-module **/

import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { Component, onWillStart, useState } from "@odoo/owl";
import { PosKanbanRenderer } from "@point_of_sale/backend/pos_kanban_view/pos_kanban_view";

export class PosDashboard extends Component {
    setup() {
        this.orm = useService("orm");
        this.actionService = useService("action");
        this.state = useState({
            data: {},
            date_start: this.today(),
            date_end: this.today(),
            currency: 'TSh',
            loading: true,
            is_manager: true,
            min_date: false,
        });

        onWillStart(async () => {
            await this.loadData();
        });
    }

    today() {
        const d = new Date();
        const year = d.getFullYear();
        const month = String(d.getMonth() + 1).padStart(2, '0');
        const day = String(d.getDate()).padStart(2, '0');
        return `${year}-${month}-${day}`;
    }

    async loadData() {
        this.state.loading = true;
        // Guard against selecting dates older than 1 week for non-managers
        if (!this.state.is_manager && this.state.min_date) {
            if (this.state.date_start < this.state.min_date) {
                this.state.date_start = this.state.min_date;
            }
            if (this.state.date_end < this.state.min_date) {
                this.state.date_end = this.state.min_date;
            }
        }
        const data = await this.orm.call("pos.dashboard.data", "get_dashboard_data", [], {
            options: {
                date_start: this.state.date_start,
                date_end: this.state.date_end
            }
        });
        if (!data) return;
        this.state.data = data;
        this.state.currency = data.currency;
        this.state.is_manager = data.is_manager !== undefined ? data.is_manager : true;
        this.state.min_date = data.min_date || false;
        if (data.date_start) {
            this.state.date_start = data.date_start;
        }
        if (data.date_end) {
            this.state.date_end = data.date_end;
        }
        this.state.loading = false;
    }

    format(value) {
        return Number(value || 0).toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2});
    }

    async applyFilters() {
        if (!this.state.is_manager && this.state.min_date) {
            if (this.state.date_start < this.state.min_date) {
                this.state.date_start = this.state.min_date;
            }
        }
        await this.loadData();
    }
    
    onOrderClick(ev) {
        const type = ev.currentTarget.dataset.type;
        const value = ev.currentTarget.dataset.value;
        this.openOrders(type, value);
    }
    
    openOrders(type, value) {
        let start = this.state.date_start;
        if (!this.state.is_manager && this.state.min_date && start < this.state.min_date) {
            start = this.state.min_date;
        }
        let domain = [['state', 'in', ['paid', 'done', 'invoiced']], ['date_order', '>=', start + ' 00:00:00'], ['date_order', '<=', this.state.date_end + ' 23:59:59']];
        let name = "Orders";
        if (type === 'date') {
            let orderDate = value;
            if (!this.state.is_manager && this.state.min_date && orderDate < this.state.min_date) {
                orderDate = this.state.min_date;
            }
            domain = [['state', 'in', ['paid', 'done', 'invoiced']], ['date_order', '>=', orderDate + ' 00:00:00'], ['date_order', '<=', orderDate + ' 23:59:59']];
            name = 'Orders on ' + orderDate;
        } else if (type === 'customer') {
            domain.push(['partner_id.name', '=', value]);
            name = 'Orders for ' + value;
        } else if (type === 'staff') {
            if (value === 'Unassigned') {
                domain.push(['user_id', '=', false]);
            } else {
                domain.push(['user_id.name', '=', value]);
            }
            name = 'Orders by ' + value;
        }

        this.actionService.doAction({
            type: 'ir.actions.act_window',
            name: name,
            res_model: 'pos.order',
            view_mode: 'list,form',
            views: [[false, 'list'], [false, 'form']],
            domain: domain,
            target: 'current',
        });
    }
}

PosDashboard.template = "custom_pos_reports.PosDashboard";
registry.category("actions").add("custom_pos_dashboard", PosDashboard);

// Attach PosDashboard as sub-component to native POS Kanban Renderer
if (PosKanbanRenderer) {
    PosKanbanRenderer.components = {
        ...PosKanbanRenderer.components,
        PosDashboard,
    };
}

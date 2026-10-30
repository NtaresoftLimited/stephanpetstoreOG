/** @odoo-module **/

import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { Component, onWillStart, useState } from "@odoo/owl";

export class GroomingDashboard extends Component {
    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.state = useState({
            stats: {
                total_appointments: 0,
                pending: 0,
                confirmed: 0,
                in_progress: 0,
                completed: 0,
                total_revenue_month: 0,
                total_expenses_month: 0,
                pending_expenses: 0,
                recent_appointments: [],
            },
        });

        onWillStart(async () => {
            await this.loadStats();
        });
    }

    async loadStats() {
        try {
            const result = await this.orm.call("grooming.appointment", "get_main_dashboard_stats", []);
            this.state.stats = result;
        } catch (error) {
            console.error("Error loading grooming dashboard stats:", error);
        }
    }

    // Navigation Methods
    openQuickAppointment() {
        this.action.doAction({
            type: 'ir.actions.act_window',
            name: 'New Appointment',
            res_model: 'grooming.appointment',
            view_mode: 'form',
            views: [[false, 'form']],
        });
    }

    openQuickExpense() {
        this.action.doAction({
            type: 'ir.actions.act_window',
            name: 'New Expense',
            res_model: 'grooming.expense',
            view_mode: 'form',
            views: [[false, 'form']],
        });
    }

    openAppointments(filter = null) {
        let context = {};
        if (filter) {
            context[`search_default_${filter}`] = 1;
        }

        this.action.doAction({
            type: 'ir.actions.act_window',
            name: 'Appointments',
            res_model: 'grooming.appointment',
            view_mode: 'list,form',
            views: [[false, 'list'], [false, 'form']],
            context: context,
        });
    }

    formatCurrency(amount) {
        return new Intl.NumberFormat('en-TZ', { style: 'currency', currency: 'TZS' }).format(amount || 0);
    }
}

GroomingDashboard.template = "grooming.GroomingDashboard";

registry.category("actions").add("grooming.main_dashboard", GroomingDashboard);

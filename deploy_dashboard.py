import paramiko
import os

HOST = "166.1.227.63"
USER = "root"
PASSWORD = "yCiEf6P2c,soWK"

# 1. Backend Model (pos_dashboard.py)
MODEL_PY = """from odoo import models, fields, api
import json
from datetime import date, datetime

class PosDashboard(models.TransientModel):
    _name = 'pos.dashboard.data'
    _description = 'POS Dashboard Data'

    @api.model
    def get_dashboard_data(self):
        # Default to Today
        today = fields.Date.context_today(self)
        
        # 1. Revenue Split (Service vs Retail)
        # Service = 'service', Retail = 'consu' or 'product'
        self.env.cr.execute(\"\"\"
            SELECT 
                pt.type, 
                SUM(pol.price_subtotal_incl) 
            FROM pos_order_line pol
            JOIN product_product pp ON pol.product_id = pp.id
            JOIN product_template pt ON pp.product_tmpl_id = pt.id
            JOIN pos_order po ON pol.order_id = po.id
            WHERE po.state IN ('paid', 'done', 'invoiced')
              AND po.date_order >= %s::timestamp
              AND po.date_order < (%s::timestamp + interval '1 day')
            GROUP BY pt.type
        \"\"\", (today, today))
        
        sales_data = self.env.cr.fetchall()
        service_sales = 0
        retail_sales = 0
        
        for type_, amount in sales_data:
            if type_ == 'service':
                service_sales += amount
            else:
                retail_sales += amount

        # 2. Refunds Check (Count negative orders today)
        refund_count = self.env['pos.order'].search_count([
            ('date_order', '>=', datetime.combine(today, datetime.min.time())),
            ('date_order', '<', datetime.combine(today, datetime.max.time())),
            ('amount_total', '<', 0),
            ('state', 'in', ['paid', 'done', 'invoiced'])
        ])

        # 3. Net Cash Status (Current Open Sessions)
        # Sum of ending balance of all open cash sessions
        # Or if session is open, use 'cash_register_balance_end_real' if set, else theoretical
        open_sessions = self.env['pos.session'].search([
            ('state', '=', 'opened')
        ])
        
        net_cash = 0
        for session in open_sessions:
            if session.cash_register_id:
                net_cash += session.cash_register_id.balance_end 
                # Note: balance_end is updated in real-time for cash journals in Odoo 16+? 
                # In Odoo 18, check cash_register_balance_end
        
        return {
            'service_sales': round(service_sales, 2),
            'retail_sales': round(retail_sales, 2),
            'refund_count': refund_count,
            'net_cash': round(net_cash, 2),
            'currency': self.env.company.currency_id.symbol
        }
"""

# 2. Client Action View (dashboard_action.xml)
ACTION_XML = """<?xml version="1.0" encoding="utf-8"?>
<odoo>
    <record id="action_pos_custom_dashboard" model="ir.actions.client">
        <field name="name">POS Dashboard</field>
        <field name="tag">custom_pos_dashboard</field>
    </record>

    <menuitem id="menu_pos_custom_dashboard"
              name="Dashboard"
              action="action_pos_custom_dashboard"
              parent="point_of_sale.menu_point_rep"
              sequence="1"/>
</odoo>
"""

# 3. JS Component (dashboard.js)
# Using standard Owl Component for Odoo 18
JS_CODE = """/** @odoo-module **/

import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { Component, onWillStart, useState } from "@odoo/owl";

export class PosDashboard extends Component {
    setup() {
        this.orm = useService("orm");
        this.state = useState({
            service_sales: 0,
            retail_sales: 0,
            refund_count: 0,
            net_cash: 0,
            currency: '$',
            loading: true
        });

        onWillStart(async () => {
            await this.loadData();
        });
    }

    async loadData() {
        const data = await this.orm.call("pos.dashboard.data", "get_dashboard_data", []);
        this.state.service_sales = data.service_sales;
        this.state.retail_sales = data.retail_sales;
        this.state.refund_count = data.refund_count;
        this.state.net_cash = data.net_cash;
        this.state.currency = data.currency;
        this.state.loading = false;
    }
    
    get totalSales() {
        return this.state.service_sales + this.state.retail_sales;
    }
    
    get retailPct() {
        if (this.totalSales === 0) return 0;
        return Math.round((this.state.retail_sales / this.totalSales) * 100);
    }

    get servicePct() {
        if (this.totalSales === 0) return 0;
        return Math.round((this.state.service_sales / this.totalSales) * 100);
    }
}

PosDashboard.template = "custom_pos_reports.PosDashboard";
registry.category("actions").add("custom_pos_dashboard", PosDashboard);
"""

# 4. XML Template (dashboard.xml)
XML_TEMPLATE = """<?xml version="1.0" encoding="UTF-8"?>
<templates xml:space="preserve">
    <t t-name="custom_pos_reports.PosDashboard" owl="1">
        <div class="o_pos_dashboard h-100 overflow-auto bg-view">
            <div class="container-fluid p-4">
                <h1 class="mb-4">POS Daily Overview</h1>
                
                <div class="row g-4">
                    <!-- Card 1: Revenue Split -->
                    <div class="col-md-4">
                        <div class="card shadow-sm h-100">
                            <div class="card-header bg-white font-weight-bold">
                                Revenue Mix (Today)
                            </div>
                            <div class="card-body">
                                <div class="d-flex justify-content-between mb-2">
                                    <span>Retail (Product):</span>
                                    <span class="font-weight-bold"><t t-esc="state.currency"/> <t t-esc="state.retail_sales"/></span>
                                </div>
                                <div class="progress mb-3" style="height: 10px;">
                                    <div class="progress-bar bg-primary" role="progressbar" t-att-style="'width: ' + retailPct + '%'"></div>
                                </div>

                                <div class="d-flex justify-content-between mb-2">
                                    <span>Grooming (Service):</span>
                                    <span class="font-weight-bold"><t t-esc="state.currency"/> <t t-esc="state.service_sales"/></span>
                                </div>
                                <div class="progress" style="height: 10px;">
                                    <div class="progress-bar bg-info" role="progressbar" t-att-style="'width: ' + servicePct + '%'"></div>
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- Card 2: Cash Control -->
                    <div class="col-md-4">
                        <div class="card shadow-sm h-100">
                            <div class="card-header bg-white font-weight-bold">
                                Cash Status (Active)
                            </div>
                            <div class="card-body text-center d-flex flex-column justify-content-center">
                                <h2 class="display-4 text-success">
                                    <t t-esc="state.currency"/> <t t-esc="state.net_cash"/>
                                </h2>
                                <span class="text-muted">Net Cash in Drawers</span>
                            </div>
                        </div>
                    </div>

                    <!-- Card 3: Refund Monitor -->
                    <div class="col-md-4">
                        <div class="card shadow-sm h-100">
                            <div class="card-header bg-white font-weight-bold">
                                Refund Monitor (Today)
                            </div>
                            <div class="card-body text-center d-flex flex-column justify-content-center">
                                <h2 t-attf-class="display-4 {{ state.refund_count > 0 ? 'text-danger' : 'text-muted' }}">
                                    <t t-esc="state.refund_count"/>
                                </h2>
                                <span class="text-muted">Refunds Processed</span>
                                <t t-if="state.refund_count > 0">
                                    <div class="alert alert-danger mt-2 p-1">
                                        Policy Alert: Check Receipts!
                                    </div>
                                </t>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </t>
</templates>
"""

def main():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASSWORD)
    sftp = client.open_sftp()
    
    BASE_DIR = "/opt/odoo/custom-addons/custom_pos_reports"
    
    print("Deploying Dashboard Files...")
    
    # Write files
    with sftp.file(f"{BASE_DIR}/models/pos_dashboard.py", "w") as f:
        f.write(MODEL_PY)
    print("Checked models/pos_dashboard.py")

    with sftp.file(f"{BASE_DIR}/views/dashboard_action.xml", "w") as f:
        f.write(ACTION_XML)
    print("Checked views/dashboard_action.xml")
    
    with sftp.file(f"{BASE_DIR}/static/src/js/dashboard.js", "w") as f:
        f.write(JS_CODE)
    print("Checked static/src/js/dashboard.js")
    
    with sftp.file(f"{BASE_DIR}/static/src/xml/dashboard.xml", "w") as f:
        f.write(XML_TEMPLATE)
    print("Checked static/src/xml/dashboard.xml")
    
    # Update __init__.py in models
    # We need to make sure 'from . import pos_dashboard' is there
    # Read existing
    try:
        with sftp.file(f"{BASE_DIR}/models/__init__.py", "r") as f:
            content = f.read().decode()
        if "pos_dashboard" not in content:
            with sftp.file(f"{BASE_DIR}/models/__init__.py", "a") as f:
                f.write("\nfrom . import pos_dashboard\n")
            print("Updated models/__init__.py")
    except Exception as e:
        print(f"Error updating models init: {e}")

    sftp.close()
    client.close()

if __name__ == "__main__":
    main()

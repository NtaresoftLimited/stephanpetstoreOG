import re

with open(r'D:\CODEX\STEPHANS OG\stephans-pet-app\grooming\static\src\xml\request_stock_popup.xml', 'r', encoding='utf-8') as f:
    xml_code = f.read()

# I will rewrite the entire xml content to perfectly match Picture 1
new_xml = '''<?xml version="1.0" encoding="UTF-8"?>
<templates id="template" xml:space="preserve">
    <t t-name="grooming.RequestStockPopup">
        <Dialog title="props.title">
            <div class="form-group p-3">
                
                <!-- Add Products Section -->
                <div class="mb-3 text-start position-relative">
                    <label class="form-label text-start w-100 fw-bold">Add Products <span class="text-danger">*</span></label>
                    <input type="text" class="form-control" placeholder="Search by product name, SKU, or barcode..." 
                           t-model="state.searchQuery" t-on-input="onSearchProduct" />
                    
                    <!-- Search Results Dropdown -->
                    <div t-if="state.searchResults.length > 0" class="list-group position-absolute w-100" style="z-index: 1000; max-height: 200px; overflow-y: auto; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                        <t t-foreach="state.searchResults" t-as="product" t-key="product.id">
                            <button type="button" class="list-group-item list-group-item-action" t-on-click="() => this.addProduct(product)">
                                <t t-esc="product.display_name" />
                            </button>
                        </t>
                    </div>
                </div>

                <!-- Product Table -->
                <div class="mb-3 text-start">
                    <table class="table table-sm table-striped mt-2 border-bottom">
                        <thead>
                            <tr>
                                <th>Product</th>
                                <th class="text-end">Qty</th>
                            </tr>
                        </thead>
                        <tbody>
                            <t t-if="state.cartLines.length === 0">
                                <tr>
                                    <td colspan="2" class="text-center text-muted py-3 border-bottom">No products added yet.</td>
                                </tr>
                            </t>
                            <t t-foreach="state.cartLines" t-as="line" t-key="line.product_id">
                                <tr>
                                    <td class="align-middle"><t t-esc="line.product_name" /></td>
                                    <td class="text-end align-middle">
                                        <div class="input-group input-group-sm justify-content-end" style="width: 120px; float: right;">
                                            <button class="btn btn-outline-secondary" type="button" t-on-click="() => this.updateQty(line, -1)">-</button>
                                            <input type="text" class="form-control text-center px-1" t-model="line.qty" t-on-change="(e) => this.onQtyChange(line, e)" />
                                            <button class="btn btn-outline-secondary" type="button" t-on-click="() => this.updateQty(line, 1)">+</button>
                                            <button class="btn btn-outline-danger ms-1" type="button" t-on-click="() => this.removeProduct(line)"><i class="fa fa-trash"></i></button>
                                        </div>
                                    </td>
                                </tr>
                            </t>
                        </tbody>
                    </table>
                </div>

                <!-- Request From (Source) -->
                <div class="mb-3 text-start">
                    <label class="form-label text-start w-100 fw-bold">Request From (Source)</label>
                    <select class="form-select" t-model="state.sourceWarehouseId">
                        <option value="" disabled="1" selected="1">Select a Warehouse...</option>
                        <t t-foreach="state.warehouses" t-as="wh" t-key="wh.id">
                            <option t-att-value="wh.id"><t t-esc="wh.name" /></option>
                        </t>
                    </select>
                </div>

                <!-- Destination Location -->
                <div class="mb-3 text-start">
                    <label class="form-label text-start w-100 fw-bold">Destination Location</label>
                    <input type="text" class="form-control bg-white" t-att-value="state.destinationWarehouseName" readonly="1" disabled="1" />
                    <small class="text-muted mt-1 d-block">Destination Location Auto-Detected from the point of sale warehouse</small>
                </div>
            </div>
            <t t-set-slot="footer">
                <button class="btn text-white" style="background-color: #6a4a5b;" t-on-click="confirm">
                    Send Request
                </button>
                <button class="btn btn-light border" t-on-click="cancel">
                    Cancel
                </button>
            </t>
        </Dialog>
    </t>
</templates>
'''

with open(r'D:\CODEX\STEPHANS OG\stephans-pet-app\grooming\static\src\xml\request_stock_popup.xml', 'w', encoding='utf-8') as f:
    f.write(new_xml)

# Now JS
with open(r'D:\CODEX\STEPHANS OG\stephans-pet-app\grooming\static\src\js\request_stock_popup.js', 'r', encoding='utf-8') as f:
    js_code = f.read()

new_js = '''/** @odoo-module */

import { Component, useState, onWillStart } from "@odoo/owl";
import { _t } from "@web/core/l10n/translation";
import { useService } from "@web/core/utils/hooks";
import { Dialog } from "@web/core/dialog/dialog";
import { AlertDialog } from "@web/core/confirmation_dialog/confirmation_dialog";

export class RequestStockPopup extends Component {
    static template = "grooming.RequestStockPopup";
    static components = { Dialog };
    
    setup() {
        super.setup();
        this.orm = useService("orm");
        this.notification = useService("notification");
        this.dialog = useService("dialog");
        
        this.state = useState({
            sourceWarehouseId: "",
            warehouses: [],
            destinationWarehouseName: "Loading...",
            destinationWarehouseId: null,
            cartLines: [],
            searchQuery: "",
            searchResults: [],
        });

        onWillStart(async () => {
            // Load warehouses
            this.state.warehouses = await this.orm.call("stock.warehouse", "search_read", [[]], {
                fields: ["id", "name"],
            });
            
            // Get current POS destination warehouse
            if (this.props.pos && this.props.pos.config && this.props.pos.config.id) {
                const configs = await this.orm.call("pos.config", "read", [this.props.pos.config.id], {
                    fields: ["warehouse_id"],
                });
                if (configs.length > 0 && configs[0].warehouse_id) {
                    this.state.destinationWarehouseId = configs[0].warehouse_id[0];
                    this.state.destinationWarehouseName = configs[0].warehouse_id[1];
                } else {
                    this.state.destinationWarehouseName = "Unknown Warehouse";
                }
            }

            // Load products from current order initially
            const currentOrder = this.props.pos.get_order();
            if (currentOrder && currentOrder.get_orderlines().length > 0) {
                this.state.cartLines = currentOrder.get_orderlines().map(line => ({
                    product_id: line.get_product().id,
                    product_name: line.get_product().display_name,
                    qty: line.get_quantity()
                }));
            }
        });
    }

    onSearchProduct(ev) {
        const query = ev.target.value;
        this.state.searchQuery = query;
        if (query.length >= 2) {
            let products = this.props.pos.db.search_product_in_category(0, query);
            this.state.searchResults = products.slice(0, 10);
        } else {
            this.state.searchResults = [];
        }
    }

    addProduct(product) {
        const existing = this.state.cartLines.find(l => l.product_id === product.id);
        if (existing) {
            existing.qty += 1;
        } else {
            this.state.cartLines.push({
                product_id: product.id,
                product_name: product.display_name,
                qty: 1
            });
        }
        this.state.searchQuery = "";
        this.state.searchResults = [];
    }

    updateQty(line, amount) {
        let newQty = parseFloat(line.qty) + amount;
        if (newQty < 1) newQty = 1;
        line.qty = newQty;
    }

    onQtyChange(line, ev) {
        let val = parseFloat(ev.target.value);
        if (isNaN(val) || val < 1) val = 1;
        line.qty = val;
    }

    removeProduct(lineToRemove) {
        this.state.cartLines = this.state.cartLines.filter(line => line.product_id !== lineToRemove.product_id);
    }

    async confirm() {
        if (this.state.cartLines.length === 0) {
            this.notification.add("No products added. Add products to request.", { type: "danger" });
            return;
        }
        if (!this.state.sourceWarehouseId) {
            this.notification.add("Please select a source warehouse.", { type: "danger" });
            return;
        }
        
        const payload = {
            source_warehouse_id: parseInt(this.state.sourceWarehouseId),
            destination_warehouse_id: this.state.destinationWarehouseId,
            lines: this.state.cartLines.map(l => ({
                product_id: l.product_id,
                qty: parseFloat(l.qty)
            }))
        };
        
        try {
            await this.orm.call("stock.picking", "create_transfer_from_pos", [payload]);
            this.notification.add("Stock Transfer Created Successfully!", { type: "success" });
            
            // Clear the cart if we started with cart items
            const currentOrder = this.props.pos.get_order();
            if (currentOrder) {
                // optional: if they wanted to clear pos cart. 
                // Let's leave it clearing cart just in case they requested from cart
                this.props.pos.removeOrder(currentOrder);
                this.props.pos.add_new_order();
            }
            
            this.props.close();
        } catch (error) {
            this.dialog.add(AlertDialog, {
                title: 'Error',
                body: 'Failed to submit request: ' + (error.data?.message || error.message || 'Unknown error'),
            });
        }
    }

    cancel() {
        this.props.close();
    }
}
'''

with open(r'D:\CODEX\STEPHANS OG\stephans-pet-app\grooming\static\src\js\request_stock_popup.js', 'w', encoding='utf-8') as f:
    f.write(new_js)

print("SUCCESS: UI XML and JS updated.")

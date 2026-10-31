/** @odoo-module */

import { Component, useState, onWillStart } from "@odoo/owl";
import { _t } from "@web/core/l10n/translation";
import { useService } from "@web/core/utils/hooks";
import { Dialog } from "@web/core/dialog/dialog";
import { AlertDialog } from "@web/core/confirmation_dialog/confirmation_dialog";

export class ReplenishmentRequestPopup extends Component {
    static template = "grooming.ReplenishmentRequestPopup";
    static components = { Dialog };
    
    setup() {
        super.setup();
        this.orm = useService("orm");
        this.notification = useService("notification");
        this.dialog = useService("dialog");
        
        this.state = useState({
            cartLines: [],
            searchQuery: "",
            searchResults: [],
            stockAvailability: {}, // { product_id: qty }
        });

        onWillStart(async () => {
            // Get products from current order
            const currentOrder = this.props.pos.get_order();
            if (currentOrder && currentOrder.get_orderlines().length > 0) {
                this.state.cartLines = currentOrder.get_orderlines().map(line => ({
                    product_id: line.get_product().id,
                    product_name: line.get_product().display_name,
                    qty: line.get_quantity()
                }));
                const pids = this.state.cartLines.map(l => l.product_id);
                await this.fetchStockAvailability(pids);
            }
        });
    }

    async fetchStockAvailability(productIds) {
        if (!productIds || productIds.length === 0) return;
        const toFetch = productIds.filter(id => !(id in this.state.stockAvailability));
        if (toFetch.length === 0) return;
        try {
            const availMap = await this.orm.call("stock.picking", "get_backstore_stock_availability", [toFetch]);
            if (availMap) {
                Object.assign(this.state.stockAvailability, availMap);
            }
        } catch (e) {
            console.warn("Failed to fetch backstore stock availability:", e);
        }
    }

    onSearchInput(ev) {
        const query = ev.target.value.trim().toLowerCase();
        this.state.searchQuery = ev.target.value;
        if (query.length >= 2) {
            let results = [];
            if (this.props.pos.db && this.props.pos.db.product_by_id) {
                const posProducts = this.props.pos.db.product_by_id;
                for (let id in posProducts) {
                    if (posProducts[id].display_name && posProducts[id].display_name.toLowerCase().includes(query)) {
                        results.push(posProducts[id]);
                    }
                    if (results.length > 10) break;
                }
            } else if (this.props.pos.models && this.props.pos.models['product.product']) {
                const posProducts = this.props.pos.models['product.product'].getAll();
                for (let product of posProducts) {
                    if (product.display_name && product.display_name.toLowerCase().includes(query)) {
                        results.push(product);
                    }
                    if (results.length > 10) break;
                }
            }
            this.state.searchResults = results;
            if (results.length > 0) {
                this.fetchStockAvailability(results.map(p => p.id));
            }
        } else {
            this.state.searchResults = [];
        }
    }

    addProduct(product) {
        const existing = this.state.cartLines.find(l => l.product_id === product.id);
        if (existing) {
            existing.qty = parseFloat(existing.qty) + 1;
        } else {
            this.state.cartLines.push({
                product_id: product.id,
                product_name: product.display_name,
                qty: 1
            });
            if (!(product.id in this.state.stockAvailability)) {
                this.fetchStockAvailability([product.id]);
            }
        }
        this.state.searchQuery = "";
        this.state.searchResults = [];
    }

    setMaxQty(line) {
        const avail = this.state.stockAvailability[line.product_id] || 0;
        if (avail > 0) {
            line.qty = avail;
        }
    }

    isQtyExceeded(line) {
        const avail = this.state.stockAvailability[line.product_id];
        if (avail === undefined || avail === null) return false;
        return parseFloat(line.qty) > avail;
    }

    updateQty(line, newQty) {
        let val = parseFloat(newQty);
        if (isNaN(val) || val <= 0) val = 1;
        line.qty = val;
    }

    removeLine(line) {
        this.state.cartLines = this.state.cartLines.filter(l => l.product_id !== line.product_id);
    }

    async confirm() {
        if (this.state.cartLines.length === 0) {
            this.notification.add("No products selected. Add products to request.", { type: "danger" });
            return;
        }

        const payload = {
            lines: this.state.cartLines.map(l => ({
                product_id: l.product_id,
                qty: l.qty
            }))
        };
        
        try {
            await this.orm.call("stock.picking", "create_replenishment_from_pos", [payload]);
            this.notification.add("Replenishment Request Submitted Successfully!", { type: "success" });
            
            // Clear the cart since the request was successful
            const currentOrder = this.props.pos.get_order();
            if (currentOrder) {
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

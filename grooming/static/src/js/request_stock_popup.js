/** @odoo-module */

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
            stockAvailability: {}, // { product_id: qty }
        });

        onWillStart(async () => {
            // Get current POS destination warehouse
            if (this.props.pos && this.props.pos.config && this.props.pos.config.id) {
                const configs = await this.orm.call("pos.config", "read", [this.props.pos.config.id], {
                    fields: ["warehouse_id", "picking_type_id"],
                });
                if (configs.length > 0 && configs[0].warehouse_id) {
                    this.state.destinationWarehouseId = configs[0].warehouse_id[0];
                    this.state.destinationWarehouseName = configs[0].warehouse_id[1];
                } else if (configs.length > 0 && configs[0].picking_type_id) {
                    const pt = await this.orm.call("stock.picking.type", "read", [configs[0].picking_type_id[0]], {
                        fields: ["warehouse_id"],
                    });
                    if (pt.length > 0 && pt[0].warehouse_id) {
                        this.state.destinationWarehouseId = pt[0].warehouse_id[0];
                        this.state.destinationWarehouseName = pt[0].warehouse_id[1];
                    }
                } else {
                    this.state.destinationWarehouseName = "Unknown Warehouse";
                }
            }

            // Load warehouses (exclude current destination warehouse from source choices)
            const allWh = await this.orm.call("stock.warehouse", "search_read", [[]], {
                fields: ["id", "name", "code"],
            });
            this.state.warehouses = allWh.filter(wh => wh.id !== this.state.destinationWarehouseId);

            // Default to Masaki Back Storage (code MBS)
            const mbsWh = allWh.find(wh => wh.code === 'MBS');
            if (mbsWh) {
                this.state.sourceWarehouseId = mbsWh.id;
            } else if (this.state.warehouses.length > 0) {
                this.state.sourceWarehouseId = this.state.warehouses[0].id;
            }

            // Load products from current order initially
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
            const availMap = await this.orm.call(
                "stock.picking", 
                "get_warehouse_stock_availability", 
                [this.state.sourceWarehouseId, toFetch]
            );
            if (availMap) {
                Object.assign(this.state.stockAvailability, availMap);
            }
        } catch (e) {
            console.warn("Failed to fetch warehouse stock availability:", e);
        }
    }

    async onSourceWarehouseChange(ev) {
        this.state.sourceWarehouseId = parseInt(ev.target.value);
        this.state.stockAvailability = {};
        const pids = this.state.cartLines.map(l => l.product_id);
        if (pids.length > 0) {
            await this.fetchStockAvailability(pids);
        }
        if (this.state.searchResults.length > 0) {
            await this.fetchStockAvailability(this.state.searchResults.map(p => p.id));
        }
    }

    async onSearchProduct(ev) {
        const query = ev.target.value;
        this.state.searchQuery = query;
        if (query.length >= 2) {
            try {
                let products = await this.orm.call("product.product", "search_read", [[
                    '|', '|', 
                    ['name', 'ilike', query], 
                    ['default_code', 'ilike', query], 
                    ['barcode', 'ilike', query]
                ]], {
                    fields: ["id", "display_name"],
                    limit: 10
                });
                this.state.searchResults = products;
                if (products.length > 0) {
                    this.fetchStockAvailability(products.map(p => p.id));
                }
            } catch (error) {
                console.error("Product search failed:", error);
            }
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

/** @odoo-module */
import { onMounted, onWillUnmount } from '@odoo/owl';
import {
  ConnectionLostError,
  ConnectionAbortedError,
} from '@web/core/network/rpc';
import { _t } from '@web/core/l10n/translation';
import { patch } from '@web/core/utils/patch';
import { ProductScreen } from '@point_of_sale/app/screens/product_screen/product_screen';
import { createRelatedModels } from "@point_of_sale/app/models/related_models";
import { PosData } from "@point_of_sale/app/models/data_service";
import { registry } from "@web/core/registry";


patch(PosData.prototype, {
    _getWiseStockLocationId(configOverride = null) {
        const config = configOverride || this.models?.["pos.config"]?.getFirst?.();
        if (!config || config.stock_warehouse === "all") {
            return null;
        }
        return (
            config.in_stock_pick
            || (config.picking_type_location_id ? (config.picking_type_location_id.id || config.picking_type_location_id[0] || config.picking_type_location_id) : null)
            || null
        );
    },

    async _refreshWiseProductQuantities(records) {
        if (!records || !records.length) {
            return;
        }
        const productIds = records.map((p) => p.id).filter(Boolean);
        if (!productIds.length) {
            return;
        }
        const location = this._getWiseStockLocationId();
        const quantities = await this.orm.call(
            "product.product",
            "wise_get_product_info_pos",
            [location, productIds]
        );
        if (!quantities) {
            return;
        }
        for (const product of records) {
            const qtyData = quantities[product.id] || { qty_available: 0, virtual_available: 0 };
            product.qty_available = qtyData.qty_available;
            product.virtual_available = qtyData.virtual_available;
            if (this.records?.["product.product"]?.has(product.id)) {
                const existing = this.records["product.product"].get(product.id);
                existing.qty_available = qtyData.qty_available;
                existing.virtual_available = qtyData.virtual_available;
            }
        }
    },

    async searchRead(model, domain = [], fields = [], options = {}, queue = false) {
        const records = await super.searchRead(...arguments);
        if (model === "product.product" && records?.length) {
            await this._refreshWiseProductQuantities(records);
        }
        return records;
    },

    async read(model, ids, fields = [], options = [], queue = false) {
        const records = await super.read(...arguments);
        if (model === "product.product" && records?.length) {
            await this._refreshWiseProductQuantities(records);
        }
        return records;
    },

    async initData() {
        const modelClasses = {};
        const relations = {};
        const fields = {};
        const data = {};
        const response = await this.loadInitialData();

        // Step 1: Populate `relations`, `fields`, and `data`
        for (const [model, values] of Object.entries(response)) {
            relations[model] = values.relations;
            fields[model] = values.fields;
            data[model] = values.data;
        }

        // Add stock_quantity to fields and relations for product.product
        if (!fields["product.product"].includes("qty_available")) {
            fields["product.product"].push("qty_available");
        }
        relations["product.product"] = relations["product.product"] || {};
        relations["product.product"].qty_available = {
            name: "qty_available",
            type: "float",
            compute: false,
            related: false,
            default: 0
        };

        // Step 2: Populate `modelClasses` and update `relations`
        for (const posModel of registry.category("pos_available_models").getAll()) {
            const pythonModel = posModel.pythonModel;
            const extraFields = posModel.extraFields || {};

            modelClasses[pythonModel] = posModel;
            relations[pythonModel] = {
                ...relations[pythonModel],
                ...extraFields,
            };
        }

        // Step 3: Generate `models`, `records`, and `indexedRecords`
        const { models, records, indexedRecords } = createRelatedModels(
            relations,
            modelClasses,
            this.opts
        );

        this.records = records;
        this.indexedRecords = indexedRecords;
        this.fields = fields;
        this.relations = relations;
        this.models = models;

        const order = data["pos.order"] || [];
        const orderlines = data["pos.order.line"] || [];

        delete data["pos.order"];
        delete data["pos.order.line"];

        this.models.loadData(data, this.modelToLoad);
        this.models.loadData({ "pos.order": order, "pos.order.line": orderlines });

        // Step 4: Fetch product quantities for all products in bulk
        const products = data["product.product"] || [];
        const productIds = products.map(product => product.id);
        const configData = (data['pos.config'] && data['pos.config'][0]) || data['pos.config'] || {};
        const location = this._getWiseStockLocationId(configData);

        // Call wise_get_product_info_pos with location and product IDs
        const quantities = await this.orm.call("product.product", "wise_get_product_info_pos", [location, productIds]);

        // Update each product with its accurate location stock quantity
        for (const product of products) {
            const qty_data = quantities[product.id] || { qty_available: 0, virtual_available: 0 };
            product.qty_available = qty_data.qty_available;
            product.virtual_available = qty_data.virtual_available;

            if (this.records["product.product"].has(product.id)) {
                const existingProduct = this.records["product.product"].get(product.id);
                existingProduct.qty_available = qty_data.qty_available;
                existingProduct.virtual_available = qty_data.virtual_available;
            } else {
                this.records["product.product"].set(product.id, product);
            }
        }

        const dbData = await this.loadIndexedDBData();
        this.loadedIndexedDBProducts = dbData ? dbData["product.product"] : [];
        this.network.loading = false;
    }
});

patch(ProductScreen.prototype, {
  setup() {
    super.setup(...arguments);

    onMounted(() => {
      if (this.pos.config.update_stock_quantities === 'real') {
        const refreshRate = this.pos.config.stock_quantities_refresh_rate;
        const refreshRateMS = (refreshRate && Number(refreshRate) * 60000) || 60000;
        this._runUpdateProductQtyTimer(refreshRateMS);
        this.loadLatestProductQtyFromDB();
      }
    });
    onWillUnmount(() => {
      if (this.updateProductQtyTimer) {
        clearInterval(this.updateProductQtyTimer);
      }
    });
  },
  _runUpdateProductQtyTimer(time = 60000) {
    this.updateProductQtyTimer = setInterval(() => {
      this.loadLatestProductQtyFromDB();
    }, time);
  },

  async loadLatestProductQtyFromDB() {
    try {
      const all_products = this.pos.models["product.product"].getAll();
      if (!all_products || !all_products.length) return;
      await this.pos.data._refreshWiseProductQuantities(all_products);
    } catch (error) {
      if (
        error instanceof ConnectionLostError ||
        error instanceof ConnectionAbortedError
      ) {
        console.warn('Network error while updating product quantities in background. Ignoring.');
      } else {
        console.warn('Other error while updating product qty:', error);
      }
    }
  },

});

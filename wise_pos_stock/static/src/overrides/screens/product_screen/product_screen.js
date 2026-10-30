/** @odoo-module */
import { onMounted, onWillUnmount } from '@odoo/owl';
import {
  ConnectionLostError,
  ConnectionAbortedError,
} from '@web/core/network/rpc';
import { _t } from '@web/core/l10n/translation';
import { patch } from '@web/core/utils/patch';
import { handleRPCError } from "@point_of_sale/app/errors/error_handlers";
import { ProductScreen } from '@point_of_sale/app/screens/product_screen/product_screen';
import { createRelatedModels } from "@point_of_sale/app/models/related_models";
import { PosData } from "@point_of_sale/app/models/data_service";
import { registry } from "@web/core/registry";


patch(PosData.prototype, {
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
        const warehouse = await this.orm.call('stock.warehouse', 'search_read', [[['id', '=', response['pos.config']['data'][0].warehouse_id]]], { limit: 1 });
//        const location = warehouse[0].lot_stock_id[0];
        const location = data['pos.config'].picking_type_location_id;

        // Call nt_get_product_info_pos with all product IDs at once
        const quantities = await this.orm.call("product.product", "wise_get_product_info_pos", [location, productIds]);

        // Update each product with its stock quantity
        for (const product of products) {
            product.qty_available = quantities[product.id] || 0;
            // this.records["product.product"].set(product.id, product);

            if (this.records["product.product"].has(product.id)) {
                const existingProduct = this.records["product.product"].get(product.id);
                existingProduct.qty_available = quantities[product.id] || 0; // Update stock_quantity directly
            } else {
                // If the product doesn't exist in the records, you can add it
                product.qty_available = quantities[product.id] || 0; // Set the stock_quantity if adding
                this.records["product.product"].set(product.id, product); // Add the product
            }
        }
//         this.records["product.product"] = products; // Ensure this is stored for global product access


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
        const refreshRateMS = refreshRate && refreshRate * 60000;
        this._runUpdateProductQtyTimer(refreshRateMS);
        this.loadLatestProductQtyFromDB();
      }
    });
    onWillUnmount(() => {
      if (this.pos.config.update_stock_quantities === 'real') {
        clearInterval(this.updateProductQtyTimer);
      }
    });
  },
  _runUpdateProductQtyTimer(time = 180000) {
    this.updateProductQtyTimer = setInterval(() => {
      this.loadLatestProductQtyFromDB();
    }, time);
  },

  async loadLatestProductQtyFromDB() {
    try {
      let kwargs = {};
      const all_products = this.pos.models["product.product"].getAll();
      const productIds = Object.keys(this.pos.models["product.product"].getAll());
      var data = []
      for (let key in all_products) {
        data.push(all_products[key].id)
      }
      if (this.pos.config.stock_warehouse === 'current') {
        kwargs.context = {
          location: this.pos.config.in_stock_pick,
        };
      }
//       const quantities = await this.pos.data.orm.call("product.product", "wise_get_product_info_pos", [location, productIds]);
      const products = await this.pos.data.orm.searchRead(
        'product.product',
        [['id', 'in', data]],
        ['qty_available', 'virtual_available'],
        kwargs
      );
      if (products && products.length > 0) {
        const productMap = new Map();
        all_products.forEach(item => productMap.set(item.id, item));
        products.forEach((product) => {
          const result = productMap.get(product.id);
          if (result) {
            result.qty_available = product.qty_available;
            result.virtual_available = product.virtual_available;
          }
        });
      }
    } catch (error) {
      if (
        error instanceof ConnectionLostError ||
        error instanceof ConnectionAbortedError
      ) {
        //TODO: Change Message
        return this.popup.add(OfflineErrorPopup, {
          title: _t('Network Error'),
          body: _t(
            'Product is not loaded. Tried loading the product from the server but there is a network error.'
          ),
        });
      } else {
        throw error;
      }
    }
  },

});
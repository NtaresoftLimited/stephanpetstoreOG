import re

with open(r'D:\CODEX\STEPHANS OG\stephans-pet-app\grooming\static\src\js\request_stock_popup.js', 'r', encoding='utf-8') as f:
    js_code = f.read()

old_func = '''    onSearchProduct(ev) {
        const query = ev.target.value;
        this.state.searchQuery = query;
        if (query.length >= 2) {
            let products = this.props.pos.db.search_product_in_category(0, query);
            this.state.searchResults = products.slice(0, 10);
        } else {
            this.state.searchResults = [];
        }
    }'''

new_func = '''    async onSearchProduct(ev) {
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
            } catch (error) {
                console.error("Product search failed:", error);
            }
        } else {
            this.state.searchResults = [];
        }
    }'''

if old_func in js_code:
    js_code = js_code.replace(old_func, new_func)
    with open(r'D:\CODEX\STEPHANS OG\stephans-pet-app\grooming\static\src\js\request_stock_popup.js', 'w', encoding='utf-8') as f:
        f.write(js_code)
    print("SUCCESS")
else:
    print("ERROR: old block not found")

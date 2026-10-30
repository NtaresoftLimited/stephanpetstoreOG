import openpyxl

wb = openpyxl.load_workbook(r"C:\Users\fisto\Downloads\Stephans pet store, Both Sotore Product (product.template).xlsx", data_only=True)
sheet = wb.active
headers = [sheet.cell(row=1, column=c).value for c in range(1, sheet.max_column + 1)]

products = []
current_prod = None

for r in range(2, sheet.max_row + 1):
    name = sheet.cell(row=r, column=headers.index('Name') + 1).value
    if name:
        current_prod = {
            'row': r,
            'name': name.strip(),
            'sku': sheet.cell(row=r, column=headers.index('Internal Reference') + 1).value,
            'price': sheet.cell(row=r, column=headers.index('Sales Price') + 1).value,
            'cost': sheet.cell(row=r, column=headers.index('Cost') + 1).value,
            'pos_category': [sheet.cell(row=r, column=headers.index('Point of Sale Category') + 1).value],
            'available_in_pos': sheet.cell(row=r, column=headers.index('Available in POS') + 1).value,
            'product_category': sheet.cell(row=r, column=headers.index('Product Category') + 1).value,
            'product_type': sheet.cell(row=r, column=headers.index('Product Type') + 1).value,
            'stock': sheet.cell(row=r, column=headers.index('Quantity On Hand') + 1).value,
            'active': sheet.cell(row=r, column=headers.index('Active') + 1).value,
            'approval_status': sheet.cell(row=r, column=headers.index('Approval Status') + 1).value,
        }
        if current_prod['sku']:
            current_prod['sku'] = str(current_prod['sku']).strip()
        products.append(current_prod)
    else:
        # Continuation row
        pos_cat = sheet.cell(row=r, column=headers.index('Point of Sale Category') + 1).value
        if pos_cat and current_prod:
            current_prod['pos_category'].append(pos_cat)

print(f"Total parsed products: {len(products)}")
print(f"Sample product 1: {products[0]}")
print(f"Sample product with multiple pos categories: {[p for p in products if len(p['pos_category']) > 1][0]}")

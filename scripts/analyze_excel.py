import openpyxl

wb = openpyxl.load_workbook(r"C:\Users\fisto\Downloads\Stephans pet store, Both Sotore Product (product.template).xlsx", data_only=True)
sheet = wb.active

headers = [sheet.cell(row=1, column=c).value for c in range(1, sheet.max_column + 1)]
print("Headers:", headers)

rows = []
for r in range(2, sheet.max_row + 1):
    row_data = {headers[c-1]: sheet.cell(row=r, column=c).value for c in range(1, sheet.max_column + 1)}
    rows.append(row_data)

print(f"Total rows in Excel: {len(rows)}")

names = [r['Name'] for r in rows if r['Name']]
skus = [r['Internal Reference'] for r in rows if r['Internal Reference']]
active = [r for r in rows if r['Active']]
sales_ok = [r for r in rows if r['Sales']]

print(f"Unique names: {len(set(names))} / {len(names)}")
print(f"Rows with Internal Reference: {len(skus)} (unique: {len(set(skus))})")
print(f"Active rows: {len(active)}")
print(f"Sales == True rows: {len(sales_ok)}")
print(f"Approval Statuses:", set(r['Approval Status'] for r in rows))

# Check duplicates in names
from collections import Counter
name_counts = Counter(names)
dup_names = [n for n, c in name_counts.items() if c > 1]
print(f"Duplicate names ({len(dup_names)}):", dup_names[:10])

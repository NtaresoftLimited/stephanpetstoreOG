import openpyxl

wb = openpyxl.load_workbook(r"C:\Users\fisto\Downloads\Stephans pet store, Both Sotore Product (product.template).xlsx", data_only=True)
sheet = wb.active
headers = [sheet.cell(row=1, column=c).value for c in range(1, sheet.max_column + 1)]

rows_without_name = []
for r in range(2, sheet.max_row + 1):
    val = sheet.cell(row=r, column=headers.index('Name') + 1).value
    if not val:
        row_vals = {headers[c-1]: sheet.cell(row=r, column=c).value for c in range(1, sheet.max_column + 1)}
        rows_without_name.append((r, row_vals))

print(f"Rows without name: {len(rows_without_name)}")
for r, data in rows_without_name[:10]:
    print(f"Row {r}: {data}")

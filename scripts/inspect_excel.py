import openpyxl

wb = openpyxl.load_workbook(r"C:\Users\fisto\Downloads\Stephans pet store, Both Sotore Product (product.template).xlsx", data_only=True)
print("Sheet names:", wb.sheetnames)
sheet = wb.active
print(f"Dimensions: {sheet.max_row} rows, {sheet.max_column} cols")

# Print first 5 rows
for r in range(1, min(6, sheet.max_row + 1)):
    row_vals = [sheet.cell(row=r, column=c).value for c in range(1, sheet.max_column + 1)]
    print(f"Row {r}: {row_vals}")

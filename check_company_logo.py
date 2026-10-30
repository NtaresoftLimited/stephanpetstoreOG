
print("--- CHECKING COMPANY LOGO ---")
company = env.company
print(f"Company: {company.name}")
if company.logo:
    print("Logo is SET.")
    print(f"Length: {len(company.logo)}")
else:
    print("Logo is NOT SET (False).")

# Check all companies
print("\nAll Companies:")
for c in env['res.company'].search([]):
    print(f"- {c.name}: {'Has Logo' if c.logo else 'No Logo'}")
print("--- DONE ---")

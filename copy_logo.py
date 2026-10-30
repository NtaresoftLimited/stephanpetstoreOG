
print("--- COPYING LOGO ---")
c_new = env['res.company'].search([('name', '=', "Stephan's Pet Store New")], limit=1)
c_old = env['res.company'].search([('name', '=', "Stephan's Pet Store")], limit=1)

if c_new and c_old:
    print(f"Found '{c_new.name}' (Logo: {bool(c_new.logo)})")
    print(f"Found '{c_old.name}' (Logo: {bool(c_old.logo)})")
    
    if c_new.logo and not c_old.logo:
        c_old.write({'logo': c_new.logo})
        print("SUCCESS: Copied logo from 'New' to 'Old'.")
    elif c_old.logo:
        print("Target company already has a logo.")
    else:
        print("Source company has no logo.")
else:
    print("Could not find both companies.")
env.cr.commit()
print("--- DONE ---")

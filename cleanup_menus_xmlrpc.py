import xmlrpc.client
import ssl

url = "https://erp.stephanspetstore.co.tz"
db = "Stephans"
username = "info@stephanspetstore.co.tz"
password = "Stephan@3202"

# Ignore SSL verification for self-signed certs if any (though likely valid)
context = ssl._create_unverified_context()

def main():
    print(f"Connecting to {url}...")
    common = xmlrpc.client.ServerProxy('{}/xmlrpc/2/common'.format(url), context=context)
    uid = common.authenticate(db, username, password, {})
    
    if not uid:
        print("Authentication Failed")
        return

    print(f"Authenticated with UID: {uid}")
    models = xmlrpc.client.ServerProxy('{}/xmlrpc/2/object'.format(url), context=context)

    # 1. Cleanup Weekly Report Menus
    print("\n--- Cleaning 'Weekly Report' Menus ---")
    # Find all menus with "Weekly Report" in the name (ORM handles translation search usually)
    # But search domain on translated field might need specific syntax or just works.
    menu_ids = models.execute_kw(db, uid, password, 'ir.ui.menu', 'search', [[['name', 'ilike', 'Weekly Report']]])
    
    if not menu_ids:
        print("No 'Weekly Report' menus found.")
    else:
        print(f"Found {len(menu_ids)} menus: {menu_ids}")
        
        # Get XML IDs
        for menu_id in menu_ids:
            # Check XML ID
            xml_ids = models.execute_kw(db, uid, password, 'ir.model.data', 'search_read', 
                [[['model', '=', 'ir.ui.menu'], ['res_id', '=', menu_id]]], 
                {'fields': ['module', 'name']})
            
            is_valid = False
            if xml_ids:
                print(f"  Menu {menu_id} XML ID: {xml_ids[0]['module']}.{xml_ids[0]['name']}")
                if xml_ids[0]['module'] == 'custom_pos_reports' and xml_ids[0]['name'] == 'menu_report_pos_weekly':
                    print("  -> VALID (Keep)")
                    is_valid = True
            else:
                print(f"  Menu {menu_id} has NO XML ID.")

            if not is_valid:
                print("  -> DELETING...")
                try:
                    models.execute_kw(db, uid, password, 'ir.ui.menu', 'unlink', [[menu_id]])
                    print("     Deleted.")
                except Exception as e:
                    print(f"     Failed to delete: {e}")

    # 2. Cleanup Sales Details Menus
    print("\n--- Cleaning 'Sales Details' Menus ---")
    menu_ids = models.execute_kw(db, uid, password, 'ir.ui.menu', 'search', [[['name', 'ilike', 'Sales Details']]])
    
    if not menu_ids:
         print("No 'Sales Details' menus found.")
    else:
         print(f"Found {len(menu_ids)} menus: {menu_ids}")
         for menu_id in menu_ids:
            xml_ids = models.execute_kw(db, uid, password, 'ir.model.data', 'search_read', 
                [[['model', '=', 'ir.ui.menu'], ['res_id', '=', menu_id]]], 
                {'fields': ['module', 'name']})
            
            is_valid = False
            # We have two valid ones potentially:
            # 1. Standard Odoo (Reporting > Sales Details) -> point_of_sale.menu_report_sales
            # 2. Our User one -> custom_pos_reports.menu_report_pos_details_user
            
            if xml_ids:
                full_xml_id = f"{xml_ids[0]['module']}.{xml_ids[0]['name']}"
                print(f"  Menu {menu_id} XML ID: {full_xml_id}")
                
                if full_xml_id in ['custom_pos_reports.menu_report_pos_details_user', 'point_of_sale.menu_report_sales']:
                     print("  -> VALID (Keep)")
                     is_valid = True
            else:
                print(f"  Menu {menu_id} has NO XML ID.")
                
            if not is_valid:
                # Double check parent to be safe? 
                # If it has no XML ID, it's likely a leftover or manually created.
                # Given the user wants to clean up...
                print("  -> DELETING...")
                try:
                    models.execute_kw(db, uid, password, 'ir.ui.menu', 'unlink', [[menu_id]])
                    print("     Deleted.")
                except Exception as e:
                    print(f"     Failed to delete: {e}")

if __name__ == "__main__":
    main()

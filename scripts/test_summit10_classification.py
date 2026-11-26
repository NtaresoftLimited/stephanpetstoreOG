import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from remote_exec import run_odoo_script

script = """
p = env['product.template'].sudo().search([('name', 'ilike', 'Summit 10')], limit=1)

test_cases = [
    ('https://summit10.com/wp-content/uploads/adult-cat-fresh-chicken-nutritional-information.jpg', 'Nutritional panel and analytical constituents', 'back', True),
    ('https://summit10.com/wp-content/uploads/adult-cat-fresh-chicken-daily-dosage.jpg', 'Daily dosage and feeding instructions', 'detail', True),
    ('https://summit10.com/wp-content/uploads/adult-cat-fresh-chicken-kibble-closeup.png', 'Kibble close-up texture detail', 'detail', True),
    ('https://summit10.com/wp-content/uploads/mobility-composition-additives.jpg', 'Composition and additives panel', 'back', True),
    ('https://summit10.com/wp-content/uploads/mobility-instructions-weight-dosage.jpg', 'Instructions for proper use and dosage by animal weight', 'detail', True),
    ('https://summit10.com/wp-content/uploads/ingredient-fresh-chicken-meat-icon.png', 'Ingredient graphic icon', 'rejected', False),
    ('https://summit10.com/wp-content/uploads/summit10-brand-banner-logo.jpg', 'General brand graphics', 'rejected', False),
    ('https://summit10.com/wp-content/uploads/adult-cat-fresh-chicken-front-packshot.png', 'Another front packshot view', 'front', False),
]

all_passed = True
print('===TESTING_SECONDARY_IMAGE_CLASSIFIER===')
for url, meta, exp_role, exp_valid in test_cases:
    role, evidence, is_valid = p._detect_and_validate_useful_view(url, None, existing_roles=['front'], source_metadata=meta)
    passed = (role == exp_role and is_valid == exp_valid)
    print(f"Test: {url.split('/')[-1]}")
    print(f"  Result: role={role}, valid={is_valid} | Expected: role={exp_role}, valid={exp_valid} -> {'PASS' if passed else 'FAIL'}")
    if not passed:
        all_passed = False

print(f"All Classifier Tests Passed: {all_passed}")
"""

if __name__ == '__main__':
    out, err = run_odoo_script(script)
    print(out)
    if err:
        print("ERR:", err[-300:])

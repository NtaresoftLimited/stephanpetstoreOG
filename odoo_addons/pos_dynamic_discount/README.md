# POS Dynamic Discount Module

This module enhances the discount functionality in the Odoo Point of Sale (POS) system by introducing a more robust and user-friendly discount application feature.

## Features

1. **Discount Type Selection**
   - Users can choose between percentage-based and fixed amount discounts
   - Clear interface for selecting discount type

2. **Percentage-based Discount**
   - Applies a percentage discount to the total amount
   - Properly handles tax calculations

3. **Fixed Amount Discount**
   - Deducts a fixed monetary value from the total
   - Correctly applies the specified amount as a single discount line

4. **Discount Amount Limits**
   - Configurable maximum limits for both percentage and fixed amount discounts
   - Prevents excessive discounts from being applied
   - Validation to ensure discounts don't exceed order totals

## Implementation Details

### Fixed Amount Discount
- Deducts a specific monetary value from the total order
- Applied as a single discount line rather than distributed across tax groups
- Preserves tax information from the original order lines

### Percentage Discount
- Applies a percentage of the total order amount
- Properly calculates based on the order total
- Maintains appropriate tax handling

### Discount Limits
- Maximum percentage discount configurable via POS settings (default: 100%)
- Maximum fixed amount discount configurable via POS settings (default: 1,000,000)
- Automatic validation to prevent discounts exceeding order totals

### Error Handling
- Comprehensive error handling for undefined tax objects
- Fallback mechanisms when tax information cannot be determined
- Proper validation of discount product configuration

## Backend Implementation

### Models
- Extended `pos.config` model with discount limit fields:
  - `max_percentage_discount`: Float field for maximum percentage discount
  - `max_fixed_amount_discount`: Float field for maximum fixed amount discount

### Views
- Added discount limit configuration fields to the POS settings form
- Fields are located in a "Discount Limits" group on the configuration form

### Security
- Standard Odoo security access controls apply
- No additional security restrictions needed for discount limit configuration

## Module Structure
```
pos_dynamic_discount/
├── models/
│   ├── __init__.py
│   └── pos_config.py
├── security/
│   └── ir.model.access.csv
├── static/
│   ├── description/
│   │   └── index.html
│   └── src/
│       └── js/
│           └── dynamic_discount.js
├── views/
│   └── pos_config_views.xml
├── __init__.py
├── __manifest__.py
├── README.md
```

## Usage

1. In the POS interface, click on the discount button
2. Select the discount type (Percentage or Amount)
3. Enter the discount value
4. The discount will be applied to the order

## Configuration

The discount limits can be configured in the POS settings:
- **Maximum Percentage Discount**: Set the maximum allowed percentage (e.g., 50 for 50%)
- **Maximum Fixed Amount Discount**: Set the maximum allowed fixed amount (e.g., 1000 for $1000)

To access these settings:
1. Go to Point of Sale > Configuration > Point of Sale
2. Select your POS configuration
3. Find the "Discount Limits" section on the configuration form
4. Set your desired limits

## Troubleshooting

### Common Issues

1. **Fields Not Visible**: If the discount limit fields don't appear in the POS configuration:
   - Ensure the module is properly installed and updated
   - Check that there are no XML parsing errors in the logs
   - Try upgrading the module again

2. **XML Parse Error**: If you encounter an XML parsing error during installation, it may be due to differences in the POS configuration form structure in your Odoo version. The view inheritance XPath may need to be adjusted to match your specific Odoo version.

3. **Configuration Not Saving**: If the discount limit values are not saving:
   - Check that the user has proper permissions to modify POS configuration
   - Verify that the database user has write permissions on the pos_config table

### Fixing Visibility Issues

If the discount limit fields are not appearing in the POS configuration:

1. **Check Module Status**:
   - Ensure the module is installed and in "Installed" status
   - Upgrade the module if it shows as "To upgrade"

2. **Verify View Inheritance**:
   - The current implementation places the fields in a "Discount Limits" group at the top of the configuration form
   - If they're still not visible, the XPath expression in `views/pos_config_views.xml` may need to be adjusted for your specific Odoo version

3. **Alternative XPath Expressions**:
   If the current XPath doesn't work, try these alternatives in `views/pos_config_views.xml`:
   ```xml
   <!-- Alternative 1: Place after a specific field -->
   <xpath expr="//field[@name='name']" position="after">
   
   <!-- Alternative 2: Place in notebook as a new page -->
   <xpath expr="//notebook" position="inside">
       <page string="Discount Settings" name="discount_settings">
   
   <!-- Alternative 3: Place at the end of the form -->
   <xpath expr="//sheet" position="inside">
   ```

4. **Check Odoo Logs**:
   - Look for any errors related to view inheritance or field definitions
   - Check if there are any access rights issues
   - Look for messages like "Element '<xpath expr=...' cannot be located in parent view"

5. **Manual Verification**:
   To manually verify the fields exist in the database:
   - Go to Settings > Technical > Database Structure > Models
   - Search for "pos.config"
   - Check if the fields `max_percentage_discount` and `max_fixed_amount_discount` appear in the model definition

6. **Database Verification**:
   You can also check directly in the database:
   ```sql
   SELECT * FROM ir_model_fields 
   WHERE model = 'pos.config' 
   AND name IN ('max_percentage_discount', 'max_fixed_amount_discount');
   ```

### Debugging Steps

1. **Restart Odoo Service**:
   ```bash
   sudo systemctl restart odoo
   ```

2. **Upgrade Module**:
   - Go to Apps > Update Apps List
   - Find the "POS Dynamic Discount" module
   - Click "Upgrade"

3. **Check for Errors**:
   ```bash
   tail -f /var/log/odoo/odoo-server.log
   ```
   Look for any error messages during the upgrade process

4. **Clear Browser Cache**:
   - Clear your browser cache and cookies
   - Refresh the POS configuration page

## Technical Improvements

1. **Enhanced Error Handling**
   - Added try-catch blocks around critical operations
   - Fallback calculations when primary methods fail
   - Proper logging of warnings for debugging

2. **Tax Management**
   - Improved tax object validation
   - Better handling of undefined tax scenarios
   - Preservation of tax information in discount lines

3. **Code Structure**
   - Clean separation of fixed amount and percentage discount logic
   - Simplified processing flow
   - Better code organization and comments

4. **Security & Validation**
   - Discount amount limits to prevent excessive discounts
   - Validation to ensure discounts don't exceed order totals
   - Proper input sanitization

## Fixed Issues

- Resolved TypeError when accessing `price_include` property of undefined tax objects
- Fixed incorrect application of fixed amount discounts across tax groups
- Improved handling of edge cases with missing tax information
- Added discount limit validation to prevent excessive discounts
- Implemented backend configuration for discount limits
- Fixed XML view inheritance issues
- Improved field visibility in POS configuration
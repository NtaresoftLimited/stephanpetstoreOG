# Abandoned Cart Recovery for Odoo 20

Recover lost revenue by automatically emailing customers who leave items in their eCommerce shopping carts.

## Key Features

1. **Quick Reminder Emails:**
   - Automated detection of abandoned carts using a background scheduled action (`ir.cron`).
   - Configurable delay (e.g., 30 minutes idle) before a cart is flagged.
   - Configurable initial reminder delay (e.g., 15 minutes after abandonment) and maximum reminders count.

2. **Easy Template Setup:**
   - Pre-built, high-converting responsive email template (`data/mail_template.xml`).
   - Displays real-time cart items, quantities, subtotal, and total amount.
   - Prominent **"Complete Your Purchase Now"** call-to-action button.

3. **Powerful Rich Text Editor:**
   - Fully editable via Odoo's native rich text editor and HTML view.
   - Paste custom HTML designs or edit directly with formatting tools.
   - Dynamic Jinja/QWeb placeholders: `{{ object.partner_id.name }}`, `{{ object.cart_recovery_url }}`, `{{ object.amount_total }}`.

4. **Secure 1-Click Cart Restoration:**
   - Generates unique cryptographic recovery tokens for each order.
   - Restores the customer's session cart instantly via `/shop/cart/recovery/<token>`.

5. **Recovery Tracking & Analytics:**
   - Dedicated dashboard under **Website > Orders > Abandoned Carts** and **Sales > Orders > Abandoned Carts**.
   - Tree, Form, Graph, and Pivot views to track abandoned vs. recovered revenue over time.
   - Manual reminder trigger button for sales reps.

6. **Test Email Wizard:**
   - Test your templates with sample orders before sending to real customers via **Website > Configuration > Settings**.

## Installation

1. Copy or place `stephans_abandoned_cart` into your Odoo addons path.
2. Update Apps List in Odoo Developer Mode.
3. Install **"Abandoned Cart Recovery"**.
4. Configure settings under **Website > Configuration > Settings > Abandoned Cart Recovery**.

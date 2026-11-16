# Stephan's POS WhatsApp Receipts (`stephans_pos_whatsapp`)

Odoo 20 module. It adds a **WhatsApp** button (official WhatsApp logo) next to the phone field of the POS **Send Receipt** popup, which opens from the receipt screen and from Orders.

## How it works
1. The cashier types or keeps the customer's number. Local Tanzanian formats are accepted: `0769 324 445`, `769324445`, `255769324445`, `+255 769 324 445`.
2. `pos.order.action_send_whatsapp_receipt(phone)`:
   - renders the receipt image server-side (`order_receipt_generate_image`, the same receipt as print/email, including Design 3);
   - stores it as an attachment with an access token;
   - sends it through **WaSender** (`https://wasenderapi.com/api/send-message`, `imageUrl` plus a thank-you caption);
   - logs the send on the order.
3. If the customer has no phone, the number is saved on the customer.

## Configuration
- **Settings → Point of Sale → Bills & Receipts → WhatsApp Receipts**, per till. It is on by default.
- **WaSender key:** the system parameter `stephans_whatsapp.api_key`, the same account as the other WhatsApp messages.
- **Image link:** WaSender downloads the image from `web.base.url`, which must be the public domain. The link only works with the attachment's access token.

## Notes
- Odoo Enterprise's `whatsapp_pos` (Meta Cloud API) does not exist on Odoo 20 Community; this replaces it. On production (Odoo 18) it was installed but never configured, and no receipt was ever sent.
- The PNG logo files are force-added to git, because the repo `.gitignore` ignores `*.png`.

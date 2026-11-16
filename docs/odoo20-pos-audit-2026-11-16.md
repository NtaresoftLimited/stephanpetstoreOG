# Odoo 20 Point of Sale audit and fixes (16 Nov 2026)

Audience: developers maintaining the Stephan's Pet Store Odoo 20 addons and running the Odoo 18 → 20 cutover.

Target: staging `stephans_odoo20` (Odoo 20 Community, service `odoo20-staging`, port 8079).
Production (Odoo 18, DB `Stephans`) was **not changed** by this work.

## 1. How the audit was run

1. **Static check of every custom file in the POS bundle.** Imports resolve to real Odoo 20 modules and the imported names are exported. Every `t-inherit` xpath matches its parent template. Odoo 18 API names are flagged.
2. **Real till in headless Edge.** A temporary manager user, `pos_audit`, has been archived since. Console errors and exceptions were captured while running:
   - the till opening and cashier PIN login;
   - one sale on each payment method;
   - a refund and a Sky Wallet recharge and payment;
   - the Actions dialog and the stock-request popups;
   - closing the session.
3. **Server-side tests in `odoo-bin shell` with rollback** where a live run would have side effects:
   - Masaki sales and its session close, because a session was open there;
   - stock-request submission, because it sends WhatsApp messages; `requests.post` and the wizard were stubbed.

## 2. Results

| Area | Mikocheni (browser) | Masaki (browser load + shell) |
|---|---|---|
| Till opens, no console errors | ✅ PIN login (`pos_hr`) | ✅ no employee login |
| Cash / Card / Selcom | ✅ | ✅ |
| Customer Account | ✅ after journal fix | ✅ |
| Sky Wallet create → recharge 50,000 → pay 20,000 | ✅ ledger CREDIT 50,000 / DEBIT 20,000, no duplicates | – |
| Refund | ✅ −19,999 cash | – |
| Stock leaves the right warehouse | ✅ MIKOC/Stock → Customers | ✅ MASAK/Stock → Customers |
| Out-of-stock sale blocked (`wise_pos_stock`) | ✅ | – |
| Request Stock / Replenishment | ✅ MBS → MIKOC transfer; SR to Masaki Back Storage | – |
| Session close, journals balanced | ✅ CSHK, BNK1, WKPCSH, INV, POSC, RPOSC | ✅ CSHM, BNK1, POSS, POSC |
| Actions dialog matches production | ✅ Pricelist, Cancel Order, Request Stock, Replenishment Request | ✅ |

## 3. Code fixes (in this branch)

### `pos_wallet_management` (Sky Wallet) → v20.0.2.2.0
The till code was still Odoo 18 and stopped the POS from starting (`WalletRechargeWidget` not found).
- **Moved modules:**
  - `@point_of_sale/app/store/pos_store` → `app/services/pos_store`;
  - `app/store/pos_hook` → `app/hooks/pos_hook`;
  - `app/navbar/navbar` → `app/components/navbar/navbar`.
- **Renamed APIs:** camelCase order API (`getOrder`, `setPartner`, `removePaymentline`, `remainingDue`, …).
  - Lines are added with `product_tmpl_id`.
  - `navigate()` replaces `showScreen()`.
  - `env.utils.formatCurrency` → `pos.formatCurrency`.
  - `parseUTCString` → `deserializeDateTime`.
- **OWL 3:**
  - Components only receive `this.props` through `props = useProps()`.
  - A `t-set` made outside `<Dialog>` does not reach its slot.
  - Templates must use `this.` (`this.pos`, `this.props`).
- **Payment screen:**
  - The "Use Sky Wallet" switch is rendered reactively (no jQuery DOM edits).
  - Wallet payments are capped at the balance, with a part-payment offer.
  - The method list is filtered in `displayedPaymentMethods`.
  - Balances refresh after `OrderPaymentValidation.afterOrderValidation`.
- **Customer list:** the balance and create/recharge buttons are added to both line layouts. Odoo 20 has no header row, and the old `//th[3]` xpath broke the list.
- **Server:**
  - `sync_from_ui` finds the order by `uuid`.
  - `wallet_recharge_data` is accepted as JSON text or a dict.
  - The currency falls back to the order or company currency, because the tills have no pricelist ("Expected singleton: res.currency()").
  - The `wk_wallet` product is always loaded through `product.template._load_pos_data_domain`.

### `grooming` (POS part)
- `pos_actions.xml` rewritten for the Odoo 20 `ControlButtons` template. All 7 Odoo 18 xpaths failed, which stops the POS rendering.
  - Request Stock and Replenishment Request now sit in the Actions dialog.
  - Note and Customer Note are hidden, as in production.
- Quotation / Order, Enter Code and Reward are hidden as in production by patching `PosAccessRightPlugin`.
  - `pos_hr` redefines those getters without `super`, so the patch is applied at runtime (first `ControlButtons.setup`).
  - The **Discount** button is intentionally kept: `pos_dynamic_discount` enforces its limits on it.
- Stock-request and replenishment popups: Odoo 20 order API, `useProps`, `this.` in templates, Font Awesome → `oi` icons.
- `stock_picking.py` / `stock_request.py`: `stock.move` no longer has `name`, and `product_uom` is now `uom_id`. Transfer creation and request approval failed with "Invalid field".

### `stephans_tz_address` (new module, v20.0.1.0.0)
- The 31 regions of Tanzania (ISO 3166-2:TZ codes 01–31).
- Dar es Salaam's 5 districts and 82 areas as `res.city`, named "Area, District" (e.g. "Mikocheni, Kinondoni"), plus the main towns of every other region.
- `enforce_cities` on Tanzania: City becomes a searchable list in the back office, the POS customer form and portal checkout. Every region has at least one town, so checkout is never blocked.
- New contacts default to Tanzania / Dar es Salaam (`ir.default`).

### Scripts
- `scripts/switch_coa_tz_odoo20.py` now creates the **POSS** "Point of Sale" sale journal and sets it as `pos.config.journal_id` on every till. See §4.

## 4. Data and settings fixed directly on staging

These are not code changes. Anyone rebuilding staging from scratch must repeat them, or rely on the script changes noted.

| Problem | Cause | Fix |
|---|---|---|
| Session close: "You are not allowed to create 'Journal'" | Odoo 20 posts the session's sales entry to journal **POSS** and creates it on demand; the chart switch removed it, and cashiers may not create journals | Created POSS (account 4000 Revenue); now also in `switch_coa_tz_odoo20.py` |
| Customer Account sale: "Cannot create a sale document in a non sale journal" | `pos.config.journal_id` held the cash journals CSHM/CSHK | Both tills → POSS |
| Stock for sales with a customer went to *Inter-warehouse transit* | 58 contacts from the 2026-10-22 contact import kept production location IDs (`property_stock_customer/supplier = {"1": 4}`) | Cleared; contacts use the defaults (Customers / Vendors). **The coming website-customer migration must not copy these properties.** |
| Discount settings differed from production | – | Masaki `manual_discount = False`; Mikocheni `module_pos_discount = False` (as production) |

Backups taken on the server: `/opt/odoo/backups/stephans_odoo20_before_pos_audit_202611160733.dump`, plus one archive per replaced file (`*_before_o20*`, `static_before_*`).

## 5. Open items

- **Test data left on staging:**
  - Mikocheni session 2376 holds 9 test orders (sales, a refund, a wallet recharge and payment) and 2 customer invoices;
  - wallet WALLET0006 ("Aldo's owner") holds 30,000.
  - Remove them, or restore the dump and re-apply §4.
- **WhatsApp from staging:** staging has a live `stephans_whatsapp.api_key`.
  - Request Stock (wizard) and Replenishment (direct WaSender call with a key written into `stock_picking.py`) message +255792079463.
  - Don't submit those from a staging till unless that's intended.
  - The feature-branch commit `82e17dc` moves the key to a system parameter.
- **Product data (same in production):** 46 POS products priced 0 or 1 (TropiDog/Josera/Pet Shop placeholders), and 8 product codes shared by two products.
- **Masaki Discount button:** production hides it, but it is kept on Odoo 20 because `pos_dynamic_discount` relies on it. Confirm.
- **Backend dashboards** (`custom_pos_reports`, grooming dashboard) set template variables with a top-level `t-set`. That works outside dialogs, but should be reviewed for the same OWL 3 rule.

## 6. Odoo 20 checklist for any POS module

1. Imports: `app/services/pos_store`, `app/hooks/pos_hook`, `app/components/navbar/navbar`. Run a static resolver over the bundle.
2. Every component that reads props declares `props = useProps()`. Templates use `this.props` / `this.pos`, never bare names.
3. Do not `t-set` outside a `<Dialog>` and read it inside the slot.
4. `xpath`s may only target the parent module's own template. For buttons from other modules, use their gating getters (e.g. `PosAccessRightPlugin`).
5. Icons: `<i class="oi" data-icon="material_name"/>`; Font Awesome classes render blank.
6. `stock.move`: no `name`; the UoM field is `uom_id`.
7. Clear `/web/assets/%` attachments and restart after deploying static files. Clients may need a hard reload or **Clear site data**, because the POS service worker caches the bundle.

# Stephan's Tanzania Addresses (`stephans_tz_address`)

Odoo 20 data module. It depends only on `base_address_extended`.

- **Regions:** the 31 regions of Tanzania as `res.country.state`, using codes `01`–`31` (ISO 3166-2:TZ). Dar es Salaam is `02`.
- **Cities (`res.city`):**
  - Dar es Salaam's districts: Kinondoni, Ilala, Temeke, Ubungo and Kigamboni.
  - Their main areas, named `"Area, District"` (e.g. `Mikocheni, Kinondoni`, `Masaki, Kinondoni`, `Kariakoo, Ilala`). Searching either the area or the district finds them.
  - The main town(s) of every other region, so no region's city list is ever empty. The portal checkout requires a city once `enforce_cities` is on.
- **City dropdown:** `enforce_cities` is set on Tanzania, so City becomes a searchable dropdown in contact forms, the POS "Create Partner" form and portal/checkout addresses.
- **Defaults:** new contacts default to **Tanzania / Dar es Salaam** (`ir.default` on `res.partner.country_id` / `state_id`).

The records are `noupdate="1"`, so areas added or renamed in Contacts → Configuration → Cities survive module upgrades. To add an area permanently, add a `res.city` record to `data/res_country_data.xml`.

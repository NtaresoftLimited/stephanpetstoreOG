"""Switch the Odoo 20 company from the generic chart of accounts to Tanzania (l10n_tz_account).

Run inside `odoo-bin shell` on stephans_odoo20 (dry run unless MIG_COMMIT=1):
    MIG_COMMIT=1 odoo-bin shell -c /etc/odoo/odoo20_stephans.conf -d stephans_odoo20 --no-http < switch_coa_tz_odoo20.py

Odoo only replaces a chart cleanly when the company has no journal items, so this:
  1. removes the staging test entries (listed in TEST_MOVES / TEST_PAYMENTS; anything else aborts),
  2. detaches the store journals from POS orders, payment methods, tills and the Sky Wallet
     provider (Odoo deletes every journal while switching),
  3. loads the Tanzania chart,
  4. recreates the store journals with their old names/codes and re-links everything,
  5. clears the company default sale/purchase tax: production sells tax-free (its 18% is archived).
"""
import os

COMMIT = os.environ.get("MIG_COMMIT") == "1"
TEST_MOVES = {"INV/2026/00001", "PWKPCSH/2026/00001", "PWKPCSH/2026/00002"}
TEST_PAYMENTS = {"PWKPCSH/2026/00001", "PWKPCSH/2026/00002"}
# Store journals recreated after the switch (code -> type); Card keeps using the chart's bank journal.
STORE_JOURNALS = {"CSHM": "cash", "CSHK": "cash", "WKPCSH": "cash", "POSC": "sale"}

env = env(context=dict(env.context, tracking_disable=True))  # noqa: F821
cr = env.cr
company = env["res.company"].search([], limit=1)
assert env["res.company"].search_count([]) == 1, "expected a single company"
Journal = env["account.journal"].sudo().with_context(active_test=False)

if company.chart_template == "tz":
    raise SystemExit("Company already uses the Tanzania chart.")

# ---- 1. snapshot ------------------------------------------------------------------------------
old = {j.id: {"code": j.code, "name": j.name, "type": j.type} for j in Journal.search([])}
cr.execute("select id, sale_journal from pos_order where sale_journal is not null")
order_journal = cr.fetchall()
cr.execute("select id, journal_id from pos_payment_method where journal_id is not null")
pm_journal = cr.fetchall()
cr.execute("select id, journal_id, closing_journal_id from pos_config")
cfg_journal = cr.fetchall()
provider_lines = env["account.payment.method.line"].sudo().search([("payment_provider_id", "!=", False)])
provider_journal = [(line.payment_provider_id.id, line.journal_id.code) for line in provider_lines]
print("store journals:", {v["code"]: v["name"] for v in old.values() if v["code"] in STORE_JOURNALS or v["type"] == "bank"})
print("orders per journal:", {old[j]["code"]: sum(1 for _o, x in order_journal if x == j) for j in {x for _o, x in order_journal}})
print("payment methods:", {pm: old[j]["code"] for pm, j in pm_journal})
print("tills:", [(c, old.get(j, {}).get("code"), old.get(k, {}).get("code")) for c, j, k in cfg_journal])
print("providers:", provider_journal)

# ---- 2. remove staging test entries ------------------------------------------------------------
payments = env["account.payment"].sudo().search([])
moves = env["account.move"].sudo().search([])
unexpected = set(payments.mapped("name")) - TEST_PAYMENTS | set(moves.mapped("name")) - TEST_MOVES
if unexpected:
    raise SystemExit("Refusing: non-test accounting entries exist: %s" % sorted(unexpected))
payments.action_draft()
payments.with_context(force_delete=True).unlink()
moves = moves.exists()
moves.filtered(lambda m: m.state == "posted").button_draft()
moves.with_context(force_delete=True).unlink()
assert not env["account.move.line"].sudo().search_count([]), "journal items remain"

# ---- 3. detach store journals -------------------------------------------------------------------
cr.execute("update pos_order set sale_journal = null where sale_journal is not null")
cr.execute("update pos_payment_method set journal_id = null where journal_id is not null")
# closing_journal_id is NOT NULL; relax it until the till is re-linked (restored below, same transaction).
cr.execute("alter table pos_config alter column closing_journal_id drop not null")
cr.execute("update pos_config set journal_id = null, closing_journal_id = null")
env["account.payment.method.line"].sudo().search([("payment_provider_id", "!=", False)]).write({"payment_provider_id": False})
env.invalidate_all()

# ---- 4. load the Tanzania chart ----------------------------------------------------------------
env["account.chart.template"].try_loading("tz", company, install_demo=False)
company = env["res.company"].browse(company.id)
print("chart:", company.chart_template, "fiscal country:", company.account_fiscal_country_id.code)

# ---- 5. recreate store journals and re-link ------------------------------------------------------
new_by_code = {}
for j_id, info in old.items():
    if info["code"] in STORE_JOURNALS:
        existing = Journal.search([("code", "=", info["code"]), ("company_id", "=", company.id)], limit=1)
        new_by_code[info["code"]] = existing or Journal.create({
            "name": info["name"], "code": info["code"], "type": STORE_JOURNALS[info["code"]], "company_id": company.id,
        })
bank = Journal.search([("type", "=", "bank"), ("company_id", "=", company.id)], order="id", limit=1)
assert bank, "Tanzania chart created no bank journal"
# The old POS closing (sale) journal used the sales income account; give the new one the chart's.
sales = Journal.search([("type", "=", "sale"), ("code", "=", "INV"), ("company_id", "=", company.id)], limit=1)
for code, journal in new_by_code.items():
    if journal.type == "sale" and not journal.default_account_id:
        journal.default_account_id = sales.default_account_id


def new_id(old_id):
    if not old_id:
        return None
    info = old[old_id]
    if info["code"] in new_by_code:
        return new_by_code[info["code"]].id
    if info["type"] == "bank":
        return bank.id
    raise SystemExit("No replacement for journal %s (%s)" % (info["code"], info["name"]))


for order_id, j in order_journal:
    cr.execute("update pos_order set sale_journal = %s where id = %s", (new_id(j), order_id))
for pm_id, j in pm_journal:
    cr.execute("update pos_payment_method set journal_id = %s where id = %s", (new_id(j), pm_id))
for cfg_id, j, k in cfg_journal:
    cr.execute("update pos_config set journal_id = %s, closing_journal_id = %s where id = %s", (new_id(j), new_id(k), cfg_id))
cr.execute("alter table pos_config alter column closing_journal_id set not null")
env.invalidate_all()
for prov_id, code in provider_journal:
    env["payment.provider"].sudo().browse(prov_id).journal_id = new_by_code.get(code) or bank

# ---- 6. production sells tax-free ----------------------------------------------------------------
company.write({"account_sale_tax_id": False, "account_purchase_tax_id": False})

# ---- 7. checks ---------------------------------------------------------------------------------------
env.flush_all()
cr.execute("select j.code, count(*) from pos_order o join account_journal j on j.id = o.sale_journal group by 1 order by 1")
print("orders per journal after:", cr.fetchall(), "of", len(order_journal))
for pm in env["pos.payment.method"].sudo().with_context(active_test=False).search([]):
    print("  PM", pm.name, pm.type, "->", pm.journal_id.code or "-", pm.journal_id.default_account_id.code or "")
for c in env["pos.config"].sudo().search([]):
    print("  TILL", c.name, "journal", c.journal_id.code, "closing", c.closing_journal_id.code,
          "closing account", c.closing_journal_id.default_account_id.code, c.closing_journal_id.default_account_id.name)
for p in env["payment.provider"].sudo().browse([p for p, _c in provider_journal]):
    print("  PROVIDER", p.name, "->", p.journal_id.code)
print("accounts", env["account.account"].sudo().search_count([]), "journals", Journal.search_count([]),
      "taxes", env["account.tax"].sudo().search_count([]),
      "products with sale tax", env["product.template"].sudo().with_context(active_test=False).search_count([("taxes_id", "!=", False)]),
      "default sale tax", company.account_sale_tax_id.name or "none")
cr.execute("select count(*) from pos_order where sale_journal is not null")
assert cr.fetchone()[0] == len(order_journal), "some POS orders lost their journal"

if COMMIT:
    cr.commit()
    print("COMMITTED")
else:
    cr.rollback()
    print("DRY RUN - rolled back")

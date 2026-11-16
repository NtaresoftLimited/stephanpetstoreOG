from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class LucyWebsiteNavigation(models.Model):
    _name = "lucy.website.navigation"
    _description = "LuCy Next.js Website Navigation"
    _order = "sequence, id"
    _parent_name = "parent_id"
    _parent_store = True
    _rec_name = "name"

    name = fields.Char(required=True, translate=True)
    key = fields.Char(
        required=True,
        index=True,
        help="Stable frontend key, for example dogs, cats, food or adult-dog-food.",
    )
    level = fields.Selection(
        [
            ("root", "Header Category"),
            ("group", "Mega-menu Group"),
            ("item", "Submenu Item"),
        ],
        required=True,
        default="item",
        index=True,
    )
    parent_id = fields.Many2one(
        "lucy.website.navigation",
        string="Parent Menu",
        index=True,
        ondelete="cascade",
    )
    parent_path = fields.Char(index=True)
    child_ids = fields.One2many("lucy.website.navigation", "parent_id", string="Children")
    url = fields.Char(required=True, default="/shop")
    category_id = fields.Many2one(
        "product.category",
        string="Catalog Category",
        index=True,
        ondelete="set null",
        help="Optional Odoo category represented by this navigation entry.",
    )
    sequence = fields.Integer(default=10, index=True)
    is_featured = fields.Boolean(
        string="Featured Group",
        help="Show this group in the compact mega-menu before View all is selected.",
    )
    published = fields.Boolean(default=True, index=True)
    active = fields.Boolean(default=True)

    _sql_constraints = [
        ("key_unique", "unique(key)", "Each Next.js menu key must be unique."),
    ]

    @api.constrains("level", "parent_id")
    def _check_hierarchy_level(self):
        expected_parent = {"root": False, "group": "root", "item": "group"}
        for record in self:
            expected = expected_parent[record.level]
            if not expected and record.parent_id:
                raise ValidationError(_("A header category cannot have a parent menu."))
            if expected and (not record.parent_id or record.parent_id.level != expected):
                raise ValidationError(
                    _("A %(level)s entry must belong to a %(parent)s entry.", level=record.level, parent=expected)
                )

    @api.model
    def get_published_navigation(self):
        """Return the small, stable payload consumed by the Next.js storefront."""
        records = self.sudo().search(
            [("active", "=", True), ("published", "=", True)],
            order="sequence, id",
        )
        return [
            {
                "id": record.id,
                "name": record.name,
                "key": record.key,
                "level": record.level,
                "parent_id": record.parent_id.id or None,
                "url": record.url,
                "sequence": record.sequence,
                "featured": record.is_featured,
                "category_id": record.category_id.id or None,
            }
            for record in records
        ]

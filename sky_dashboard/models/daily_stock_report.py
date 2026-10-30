from collections import defaultdict
from datetime import datetime, time, timedelta

import pytz

from odoo import _, api, fields, models
from odoo.exceptions import AccessError, UserError, ValidationError


class SkyDailyStockReport(models.Model):
    _name = "sky.daily.stock.report"
    _description = "SKY Daily Stock Report"
    _order = "report_date desc, pos_config_id"

    name = fields.Char(required=True, readonly=True, index=True)
    report_date = fields.Date(required=True, readonly=True, index=True)
    date_end = fields.Date(string="End Date", readonly=True, index=True)
    pos_config_id = fields.Many2one(
        "pos.config", required=True, readonly=True, index=True, ondelete="restrict"
    )
    warehouse_id = fields.Many2one(
        "stock.warehouse", required=True, readonly=True, index=True, ondelete="restrict"
    )
    cashier_user_ids = fields.Many2many(
        "res.users", "sky_stock_report_user_rel", "report_id", "user_id", readonly=True
    )
    state = fields.Selection(
        [("draft", "Draft"), ("locked", "Locked")],
        default="locked",
        required=True,
        readonly=True,
    )
    generated_at = fields.Datetime(default=fields.Datetime.now, required=True, readonly=True)
    generated_by_id = fields.Many2one(
        "res.users", default=lambda self: self.env.user, required=True, readonly=True
    )
    line_ids = fields.One2many(
        "sky.daily.stock.report.line", "report_id", readonly=True, copy=False
    )
    product_count = fields.Integer(compute="_compute_totals")
    total_sold_qty = fields.Float(compute="_compute_totals")
    total_returned_qty = fields.Float(compute="_compute_totals")
    total_closing_qty = fields.Float(compute="_compute_totals")

    @api.depends(
        "line_ids", "line_ids.sold_qty", "line_ids.returned_qty", "line_ids.closing_qty"
    )
    def _compute_totals(self):
        for report in self:
            report.product_count = len(report.line_ids)
            report.total_sold_qty = sum(report.line_ids.mapped("sold_qty"))
            report.total_returned_qty = sum(report.line_ids.mapped("returned_qty"))
            report.total_closing_qty = sum(report.line_ids.mapped("closing_qty"))

    def unlink(self):
        if not self.env.su and not self.env.user.has_group("sky_dashboard.group_sky_stock_manager"):
            raise AccessError(_("Daily stock reports cannot be deleted by cashiers."))
        return super().unlink()

    def write(self, vals):
        if not self.env.su and not self.env.user.has_group("sky_dashboard.group_sky_stock_manager"):
            raise AccessError(_("Daily stock reports are read-only for cashiers."))
        return super().write(vals)

    @api.model
    def _day_bounds_utc(self, report_date):
        timezone = pytz.timezone(
            self.env.context.get("tz")
            or self.env.user.tz
            or self.env.company.partner_id.tz
            or "Africa/Nairobi"
        )
        start_local = timezone.localize(datetime.combine(report_date, time.min))
        end_local = start_local + timedelta(days=1)
        return (
            start_local.astimezone(pytz.UTC).replace(tzinfo=None),
            end_local.astimezone(pytz.UTC).replace(tzinfo=None),
        )

    @api.model
    def _cashier_users(self, config, report_date=None):
        employees = config.basic_employee_ids | config.advanced_employee_ids
        users = employees.mapped("user_id").filtered(lambda user: user.active)
        if report_date:
            start_utc, end_utc = self._day_bounds_utc(report_date)
            order_users = self.env["pos.order"].sudo().search([
                ("config_id", "=", config.id),
                ("date_order", ">=", start_utc),
                ("date_order", "<", end_utc),
            ]).mapped("user_id").filtered(lambda user: user.active)
            users = users | order_users
        return users

    @api.model
    def _done_quantity(self, move):
        if "quantity" in move._fields:
            return move.quantity
        if "quantity_done" in move._fields:
            return move.quantity_done
        return move.product_uom_qty

    @api.model
    def _prepare_lines(self, config, report_date, end_date=None):
        if not end_date:
            end_date = report_date
        warehouse = config.warehouse_id
        if not warehouse:
            raise ValidationError(_("%s has no warehouse assigned.") % config.display_name)
        stock_location = warehouse.lot_stock_id
        inside_location_ids = set(
            self.env["stock.location"].sudo().search([("id", "child_of", stock_location.id)]).ids
        )
        start_utc, _ = self._day_bounds_utc(report_date)
        _, end_utc = self._day_bounds_utc(end_date)

        metrics = defaultdict(
            lambda: {"sold": 0.0, "returned": 0.0, "transfer": 0.0, "adjustment": 0.0}
        )
        order_lines = self.env["pos.order.line"].sudo().search(
            [
                ("order_id.config_id", "=", config.id),
                ("order_id.date_order", ">=", start_utc),
                ("order_id.date_order", "<", end_utc),
                ("order_id.state", "in", ["paid", "done", "invoiced"]),
                ("product_id.type", "!=", "service"),
            ]
        )
        for line in order_lines:
            line_uom = (
                line.product_uom_id
                if "product_uom_id" in line._fields and line.product_uom_id
                else line.product_id.uom_id
            )
            quantity = line_uom._compute_quantity(line.qty, line.product_id.uom_id)
            if quantity >= 0:
                metrics[line.product_id.id]["sold"] += quantity
            else:
                metrics[line.product_id.id]["returned"] += abs(quantity)

        moves = self.env["stock.move"].sudo().search(
            [
                ("state", "=", "done"),
                ("date", ">=", start_utc),
                ("date", "<", end_utc),
                ("product_id.type", "!=", "service"),
                "|",
                ("location_id", "child_of", stock_location.id),
                ("location_dest_id", "child_of", stock_location.id),
            ]
        )
        for move in moves:
            source_inside = move.location_id.id in inside_location_ids
            destination_inside = move.location_dest_id.id in inside_location_ids
            if source_inside == destination_inside:
                continue
            signed_quantity = self._done_quantity(move)
            if source_inside:
                signed_quantity *= -1
            source_usage = move.location_id.usage
            destination_usage = move.location_dest_id.usage
            if "inventory" in (source_usage, destination_usage):
                metrics[move.product_id.id]["adjustment"] += signed_quantity
            elif {source_usage, destination_usage} & {"customer"}:
                # POS sales and returns are taken from order lines for cashier accuracy.
                continue
            else:
                metrics[move.product_id.id]["transfer"] += signed_quantity

        quant_model = self.env["stock.quant"].sudo()
        quant_domain = [("location_id", "child_of", stock_location.id)]
        try:
            quant_groups = quant_model._read_group(
                quant_domain, groupby=["product_id"], aggregates=["quantity:sum"]
            )
            closing_by_product = {
                product.id: quantity for product, quantity in quant_groups if product
            }
        except Exception:
            quant_groups = quant_model.read_group(
                quant_domain,
                ["product_id", "quantity:sum"],
                ["product_id"],
                lazy=False,
            )
            closing_by_product = {
                group["product_id"][0]: group.get("quantity", 0.0)
                for group in quant_groups
                if group["product_id"]
            }

        # Reconstruct the stock at the report day's closing time. This keeps
        # manager regeneration accurate even when it is performed days later.
        later_moves = self.env["stock.move"].sudo().search(
            [
                ("state", "=", "done"),
                ("date", ">=", end_utc),
                ("product_id.type", "!=", "service"),
                "|",
                ("location_id", "child_of", stock_location.id),
                ("location_dest_id", "child_of", stock_location.id),
            ]
        )
        net_after_closing = defaultdict(float)
        for move in later_moves:
            source_inside = move.location_id.id in inside_location_ids
            destination_inside = move.location_dest_id.id in inside_location_ids
            if source_inside == destination_inside:
                continue
            quantity = self._done_quantity(move)
            net_after_closing[move.product_id.id] += quantity if destination_inside else -quantity
        for product_id, net_quantity in net_after_closing.items():
            closing_by_product[product_id] = closing_by_product.get(product_id, 0.0) - net_quantity
        product_ids = set(metrics) | {
            product_id for product_id, quantity in closing_by_product.items() if quantity
        }

        commands = []
        for product in self.env["product.product"].sudo().browse(product_ids).sorted("display_name"):
            values = metrics[product.id]
            closing = closing_by_product.get(product.id, 0.0)
            opening = (
                closing
                + values["sold"]
                - values["returned"]
                - values["transfer"]
                - values["adjustment"]
            )
            commands.append(
                fields.Command.create(
                    {
                        "product_id": product.id,
                        "opening_qty": opening,
                        "sold_qty": values["sold"],
                        "returned_qty": values["returned"],
                        "transfer_qty": values["transfer"],
                        "adjustment_qty": values["adjustment"],
                        "closing_qty": closing,
                    }
                )
            )
        return commands

    @api.model
    def generate_for_range(self, start_date, end_date=None, config_ids=None, replace=False):
        start_date = fields.Date.to_date(start_date or fields.Date.context_today(self))
        end_date = fields.Date.to_date(end_date or start_date)
        configs = (
            self.env["pos.config"].sudo().browse(config_ids).exists()
            if config_ids
            else self.env["pos.config"].sudo().search([("active", "=", True)])
        )
        reports = self.browse()
        for config in configs.filtered("warehouse_id"):
            domain = [
                ("report_date", "=", start_date),
                ("pos_config_id", "=", config.id),
            ]
            if start_date != end_date:
                domain.append(("date_end", "=", end_date))
            existing = self.sudo().search(domain, limit=1)
            if existing and not replace:
                reports |= existing
                continue
            if existing:
                existing.sudo().unlink()
            users = self._cashier_users(config, start_date)
            warehouse_name = config.warehouse_id.name or config.name
            date_label = (
                start_date.strftime("%d %b %Y")
                if start_date == end_date
                else f"{start_date.strftime('%d %b %Y')} - {end_date.strftime('%d %b %Y')}"
            )
            report = self.sudo().create(
                {
                    "name": f"Stock Report — {warehouse_name} — {date_label}",
                    "report_date": start_date,
                    "date_end": end_date,
                    "pos_config_id": config.id,
                    "warehouse_id": config.warehouse_id.id,
                    "cashier_user_ids": [fields.Command.set(users.ids)],
                    "line_ids": self._prepare_lines(config, start_date, end_date),
                    "state": "locked",
                }
            )
            reports |= report
        return reports

    @api.model
    def generate_for_date(self, report_date=None, config_ids=None, replace=False):
        d = fields.Date.to_date(report_date or fields.Date.context_today(self))
        return self.generate_for_range(d, d, config_ids=config_ids, replace=replace)

    @api.model
    def _cron_generate_daily_reports(self):
        report_model = self.with_context(tz="Africa/Nairobi")
        report_date = fields.Date.context_today(report_model) - timedelta(days=1)
        start_utc, end_utc = report_model._day_bounds_utc(report_date)
        eligible_configs = self.env["pos.config"].sudo().search(
            [("active", "=", True), ("warehouse_id", "!=", False)]
        )
        ready_config_ids = []
        for config in eligible_configs:
            open_session = self.env["pos.session"].sudo().search_count(
                [
                    ("config_id", "=", config.id),
                    ("state", "!=", "closed"),
                    ("start_at", "<", end_utc),
                    "|",
                    ("stop_at", "=", False),
                    ("stop_at", ">=", start_utc),
                ],
                limit=1,
            )
            if not open_session:
                ready_config_ids.append(config.id)
        if ready_config_ids:
            report_model.generate_for_date(report_date, ready_config_ids)

    def action_regenerate(self):
        if not self.env.user.has_group("sky_dashboard.group_sky_stock_manager"):
            raise AccessError(_("Only stock report managers can regenerate reports."))
        regenerated = self.browse()
        for report in self:
            regenerated |= self.generate_for_date(
                report.report_date, report.pos_config_id.ids, replace=True
            )
        return {
            "type": "ir.actions.act_window",
            "name": _("Cashiers Stock Report"),
            "res_model": self._name,
            "res_id": regenerated[:1].id,
            "view_mode": "form",
        }

    def action_download_pdf(self):
        return self.env.ref("sky_dashboard.action_report_sky_daily_stock").report_action(self)

class SkyDailyStockReportLine(models.Model):
    _name = "sky.daily.stock.report.line"
    _description = "SKY Daily Stock Report Line"
    _order = "product_id"

    report_id = fields.Many2one(
        "sky.daily.stock.report", required=True, ondelete="cascade", index=True
    )
    product_id = fields.Many2one(
        "product.product", required=True, readonly=True, ondelete="restrict", index=True
    )
    product_image = fields.Binary(related="product_id.image_128", readonly=True)
    opening_qty = fields.Float(readonly=True, digits="Product Unit of Measure")
    sold_qty = fields.Float(readonly=True, digits="Product Unit of Measure")
    returned_qty = fields.Float(readonly=True, digits="Product Unit of Measure")
    transfer_qty = fields.Float(readonly=True, digits="Product Unit of Measure")
    adjustment_qty = fields.Float(readonly=True, digits="Product Unit of Measure")
    closing_qty = fields.Float(readonly=True, digits="Product Unit of Measure")

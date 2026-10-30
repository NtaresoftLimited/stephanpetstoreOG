import base64
import io
from datetime import timedelta

import xlsxwriter
from odoo import _, api, fields, models
from odoo.exceptions import UserError


class SkyStockGenerateWizard(models.TransientModel):
    _name = "sky.stock.generate.wizard"
    _description = "Stock Card Report Wizard"

    start_date = fields.Date(
        string="Start Date",
        required=True,
        default=lambda self: fields.Date.context_today(self) - timedelta(days=1),
    )
    end_date = fields.Date(
        string="End Date",
        required=True,
        default=lambda self: fields.Date.context_today(self) - timedelta(days=1),
    )
    report_date = fields.Date(
        string="Report Date",
        compute="_compute_report_date",
        inverse="_inverse_report_date",
    )

    company_id = fields.Many2one(
        "res.company",
        string="Company",
        required=True,
        default=lambda self: self.env.company,
    )

    @api.depends("start_date")
    def _compute_report_date(self):
        for record in self:
            record.report_date = record.start_date

    def _inverse_report_date(self):
        for record in self:
            if record.report_date:
                record.start_date = record.report_date
                if not record.end_date or record.end_date < record.start_date:
                    record.end_date = record.report_date

    @api.model
    def _get_warehouse_options(self):
        options = [("all", _("All Warehouses"))]
        warehouses = (
            self.env["pos.config"]
            .sudo()
            .search([("active", "=", True), ("warehouse_id", "!=", False)])
            .mapped("warehouse_id")
            .sorted("name")
        )
        for w in warehouses:
            options.append((str(w.id), w.name))
        return options

    warehouse_option = fields.Selection(
        selection="_get_warehouse_options",
        string="Stock Location",
        required=True,
        default="all",
    )
    replace_existing = fields.Boolean(
        string="Regenerate Figures",
        default=True,
        help="Recalculate figures to ensure latest live stock metrics.",
    )

    def _get_target_configs(self):
        all_configs = self.env["pos.config"].sudo().search(
            [("active", "=", True), ("warehouse_id", "!=", False)]
        )
        if self.warehouse_option == "all":
            return all_configs
        return all_configs.filtered(
            lambda c: str(c.warehouse_id.id) == str(self.warehouse_option)
            or c.warehouse_id.name.lower() == str(self.warehouse_option).lower()
        )

    def _generate_reports(self):
        self.ensure_one()
        if self.start_date > self.end_date:
            raise UserError(_("Start Date cannot be after End Date."))
        if self.end_date > fields.Date.context_today(self):
            raise UserError(_("A stock report cannot be generated for a future date."))

        target_configs = self._get_target_configs()
        if not target_configs:
            raise UserError(_("No eligible warehouse or POS branch found."))

        reports = self.env["sky.daily.stock.report"].sudo().generate_for_range(
            self.start_date,
            self.end_date,
            target_configs.ids,
            replace=self.replace_existing,
        )
        if not reports:
            raise UserError(_("No reports could be generated for the selected warehouse(s)."))

        return reports.sorted(lambda r: r.warehouse_id.name)

    def action_generate_pdf(self):
        reports = self._generate_reports()
        return self.env.ref("sky_dashboard.action_report_sky_daily_stock").report_action(reports)

    def action_generate_and_download(self):
        return self.action_generate_pdf()

    def action_generate(self):
        reports = self._generate_reports()
        return {
            "type": "ir.actions.act_window",
            "name": _("Stock Card Report"),
            "res_model": "sky.daily.stock.report",
            "view_mode": "list,form",
            "domain": [("id", "in", reports.ids)],
            "context": {"search_default_group_warehouse": 1},
        }

    def action_generate_excel(self):
        reports = self._generate_reports()
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {"in_memory": True})

        title_fmt = workbook.add_format({
            "bold": True,
            "font_size": 13,
            "color": "#1e293b",
        })
        subtitle_fmt = workbook.add_format({
            "font_size": 9,
            "color": "#64748b",
        })
        header_fmt = workbook.add_format({
            "bold": True,
            "font_size": 9,
            "bg_color": "#f8fafc",
            "color": "#334155",
            "border": 1,
            "border_color": "#cbd5e1",
            "align": "center",
            "valign": "vcenter",
        })
        text_fmt = workbook.add_format({
            "font_size": 9,
            "border": 1,
            "border_color": "#e2e8f0",
            "valign": "vcenter",
        })
        num_fmt = workbook.add_format({
            "font_size": 9,
            "border": 1,
            "border_color": "#e2e8f0",
            "align": "center",
            "valign": "vcenter",
            "num_format": "#,##0",
        })
        total_label_fmt = workbook.add_format({
            "bold": True,
            "font_size": 9,
            "bg_color": "#f1f5f9",
            "color": "#1e293b",
            "border": 1,
            "border_color": "#94a3b8",
            "align": "right",
            "valign": "vcenter",
        })
        total_num_fmt = workbook.add_format({
            "bold": True,
            "font_size": 9,
            "bg_color": "#f1f5f9",
            "color": "#1e293b",
            "border": 1,
            "border_color": "#94a3b8",
            "align": "center",
            "valign": "vcenter",
            "num_format": "#,##0",
        })

        for report in reports:
            sheet_title = report.warehouse_id.name[:31]
            ws = workbook.add_worksheet(sheet_title)
            ws.set_column("A:A", 15)  # Code
            ws.set_column("B:B", 42)  # Product
            ws.set_column("C:H", 11)  # Quantities

            ws.write("A1", f"STEPHAN'S PET STORE — {report.warehouse_id.name.upper()}", title_fmt)
            date_label = (
                self.start_date.strftime("%d %b %Y")
                if self.start_date == self.end_date
                else f"{self.start_date.strftime('%d %b %Y')} to {self.end_date.strftime('%d %b %Y')}"
            )
            ws.write("A2", f"Stock Card Report | Period: {date_label} | Generated: {fields.Datetime.now().strftime('%Y-%m-%d %H:%M')}", subtitle_fmt)

            headers = ["Code", "Product", "Opening", "Sold", "Returned", "Transfers", "Adjustments", "Closing"]
            row = 4
            for c_idx, h in enumerate(headers):
                ws.write(row, c_idx, h, header_fmt)

            row += 1
            start_row = row + 1
            for line in report.line_ids:
                code = line.product_id.default_code or ""
                name = line.product_id.name or line.product_id.display_name
                ws.write(row, 0, code, text_fmt)
                ws.write(row, 1, name, text_fmt)
                ws.write(row, 2, line.opening_qty, num_fmt)
                ws.write(row, 3, line.sold_qty, num_fmt)
                ws.write(row, 4, line.returned_qty, num_fmt)
                ws.write(row, 5, line.transfer_qty, num_fmt)
                ws.write(row, 6, line.adjustment_qty, num_fmt)
                ws.write(row, 7, line.closing_qty, num_fmt)
                row += 1

            end_row = row
            ws.write(row, 0, "", total_label_fmt)
            ws.write(row, 1, f"Total ({report.warehouse_id.name})", total_label_fmt)
            for c_idx in range(2, 8):
                col_letter = chr(ord("A") + c_idx)
                ws.write_formula(row, c_idx, f"=SUM({col_letter}{start_row}:{col_letter}{end_row})", total_num_fmt)

        workbook.close()
        output.seek(0)

        loc_slug = "All_Warehouses" if self.warehouse_option == "all" else reports[0].warehouse_id.name.replace(" ", "_")
        date_slug = str(self.start_date) if self.start_date == self.end_date else f"{self.start_date}_to_{self.end_date}"
        filename = f"Stock_Card_Report_{loc_slug}_{date_slug}.xlsx"

        attachment = self.env["ir.attachment"].sudo().create({
            "name": filename,
            "type": "binary",
            "datas": base64.b64encode(output.read()),
            "res_model": "sky.stock.generate.wizard",
            "res_id": self.id,
            "mimetype": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        })

        return {
            "type": "ir.actions.act_url",
            "url": f"/web/content/{attachment.id}?download=true",
            "target": "self",
        }

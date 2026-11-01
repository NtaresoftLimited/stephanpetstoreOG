import logging
import json
import re
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from odoo import fields, http
from odoo.exceptions import UserError, ValidationError
from odoo.http import request


_logger = logging.getLogger(__name__)
NAIROBI_TZ = ZoneInfo("Africa/Nairobi")

PRICES = {
    "dog": {
        "standard": {"small": 60000, "medium": 70000, "large": 80000},
        "super_premium": {"small": 80000, "medium": 90000, "large": 100000},
    },
    "cat": {
        "standard": {"kitten": 60000, "adult": 70000, "senior": 80000},
        "super_premium": {"kitten": 80000, "adult": 90000, "senior": 100000},
    },
    "small_animal": {
        "super_premium": {
            "hamster": 100000,
            "junior_rabbit": 100000,
            "adult_rabbit": 150000,
            "guinea_pig": 100000,
        },
    },
}

BREED_SIZES = {
    "dog": [
        {"value": "small", "label": "Small Breeds"},
        {"value": "medium", "label": "Medium Breeds"},
        {"value": "large", "label": "Large Breeds"},
    ],
    "cat": [
        {"value": "kitten", "label": "Kitten - (2 - 12 Months)"},
        {"value": "adult", "label": "Adult Cat - (1+ Year)"},
        {"value": "senior", "label": "Senior Cat - (5+ Years)"},
    ],
    "small_animal": [
        {"value": "hamster", "label": "Hamster"},
        {"value": "junior_rabbit", "label": "Junior Rabbit (0 - 6 months)"},
        {"value": "adult_rabbit", "label": "Adult Rabbit (6 months +)"},
        {"value": "guinea_pig", "label": "Guinea Pig"},
    ],
}

VALID_TIMES = [
    {"value": f"{hour:02d}:{minute:02d}", "label": datetime(2000, 1, 1, hour, minute).strftime("%-I:%M %p")}
    for hour in range(9, 18)
    for minute in (0, 30)
]
VALID_TIME_VALUES = {slot["value"] for slot in VALID_TIMES}
SERVICE_XMLIDS = {
    "standard": "grooming.grooming_service_standard",
    "super_premium": "grooming.grooming_service_super",
}
PHONE_RE = re.compile(r"^(?:\+255|0)([67]\d{8})$")
EMAIL_RE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")


class StephansGroomingWebsite(http.Controller):
    @staticmethod
    def _get_website_prices():
        prices = {}
        for key, xmlid in SERVICE_XMLIDS.items():
            service = request.env.ref(xmlid, raise_if_not_found=False)
            if not service:
                continue
            for line in service.sudo().price_line_ids:
                prices.setdefault(line.species, {}).setdefault(key, {})[line.size_category] = line.price
        return prices or PRICES

    @staticmethod
    def _normalise_phone(phone):
        compact = re.sub(r"[\s()\-]", "", phone or "")
        match = PHONE_RE.fullmatch(compact)
        if not match:
            raise ValidationError("Enter a valid Tanzanian mobile number, for example 0712 345 678.")
        return "+255" + match.group(1)

    @staticmethod
    def _is_ajax():
        return request.httprequest.headers.get("X-Requested-With") == "XMLHttpRequest"

    def _error_response(self, message, status=400):
        if self._is_ajax():
            return request.make_json_response({"ok": False, "error": message}, status=status)
        return request.render("stephans_website_theme.booking_error", {"error": message}, status=status)

    @http.route(["/grooming", "/stephans-grooming"], type="http", auth="public", website=True)
    def grooming(self, **kw):
        partner = request.env.user.partner_id if not request.env.user._is_public() else request.env["res.partner"]
        now_local = datetime.now(NAIROBI_TZ)
        detangling_fee = request.env["ir.config_parameter"].sudo().get_float(
            "grooming.detangling_fee", default=30000.0
        )
        return request.render("stephans_website_theme.grooming_page", {
            "valid_times": VALID_TIMES,
            "min_date": now_local.date().isoformat(),
            "default_customer_name": partner.name or "",
            "default_customer_phone": partner.phone or "",
            "default_customer_email": partner.email or "",
            "prices_json": json.dumps(self._get_website_prices()),
            "detangling_fee": detangling_fee,
        })

    @http.route("/grooming/book", type="http", auth="public", website=True, methods=["POST"], csrf=True)
    def book(self, **post):
        required = (
            "customer_name", "customer_phone", "pet_name", "pet_type",
            "pet_category", "service_key", "preferred_date", "preferred_time",
        )
        if any(not (post.get(name) or "").strip() for name in required):
            return self._error_response("Please complete all required fields.")

        try:
            pet_type = post["pet_type"].strip()
            pet_category = post["pet_category"].strip()
            service_key = post["service_key"].strip()
            allowed_categories = {item["value"] for item in BREED_SIZES.get(pet_type, [])}
            if service_key not in SERVICE_XMLIDS or pet_category not in allowed_categories:
                raise ValidationError("The selected pet type, size or package is not valid.")
            if service_key not in PRICES.get(pet_type, {}) or pet_category not in PRICES[pet_type][service_key]:
                raise ValidationError("That package is not available for the selected pet.")

            preferred_time = post["preferred_time"].strip()
            if preferred_time not in VALID_TIME_VALUES:
                raise ValidationError("Please select one of the available appointment times.")

            local_naive = datetime.strptime(
                f"{post['preferred_date'].strip()} {preferred_time}", "%Y-%m-%d %H:%M"
            )
            appointment_local = local_naive.replace(tzinfo=NAIROBI_TZ)
            now_local = datetime.now(NAIROBI_TZ)
            if appointment_local.weekday() == 6:
                raise ValidationError("We are closed on Sundays. Please choose Monday through Saturday.")
            if appointment_local < now_local + timedelta(minutes=15):
                raise ValidationError("Please choose a time at least 15 minutes from now.")

            appointment_utc = appointment_local.astimezone(ZoneInfo("UTC")).replace(tzinfo=None)
            Appointment = request.env["grooming.appointment"].sudo()
            conflict = Appointment.search_count([
                ("appointment_date", "=", fields.Datetime.to_string(appointment_utc)),
                ("state", "!=", "cancelled"),
            ])
            if conflict:
                raise ValidationError("That appointment time is already booked. Please choose another slot.")

            phone = self._normalise_phone(post["customer_phone"])
            email = (post.get("customer_email") or "").strip().lower()
            if email and not EMAIL_RE.fullmatch(email):
                raise ValidationError("Enter a valid email address or leave it blank.")

            Partner = request.env["res.partner"].sudo()
            local_phone = "0" + phone[4:]
            phone_domain = [("phone", "in", [phone, local_phone, post["customer_phone"]])]
            if "mobile" in Partner._fields:
                phone_domain = [
                    "|",
                    ("phone", "in", [phone, local_phone, post["customer_phone"]]),
                    ("mobile", "in", [phone, local_phone, post["customer_phone"]]),
                ]
            partner = Partner.search(phone_domain, limit=1)
            partner_values = {
                "name": post["customer_name"].strip(),
                "phone": phone,
                "email": email or False,
            }
            if "mobile" in Partner._fields:
                partner_values["mobile"] = phone
            if partner:
                partner.write({key: value for key, value in partner_values.items() if value})
            else:
                partner = Partner.create(partner_values)

            service = request.env.ref(SERVICE_XMLIDS[service_key], raise_if_not_found=False)
            if not service:
                raise UserError("The selected grooming package is temporarily unavailable.")
            service = service.sudo()

            appointment = Appointment.create({
                "partner_id": partner.id,
                "pet_name": post["pet_name"].strip(),
                "pet_type": pet_type,
                "pet_category": pet_category,
                "service_type": "full_grooming",
                "service_id": service.id,
                "appointment_date": fields.Datetime.to_string(appointment_utc),
                "preferred_time": preferred_time,
                "has_detangling": post.get("has_detangling") in ("on", "1", "true"),
                "notes": (post.get("notes") or "").strip() or False,
            })

            request.env["calendar.event"].sudo().create({
                "name": f"Grooming: {appointment.pet_name} — {appointment.name}",
                "start": fields.Datetime.to_string(appointment_utc),
                "stop": fields.Datetime.to_string(appointment_utc + timedelta(hours=2)),
                "partner_ids": [(6, 0, [partner.id])],
                "description": (
                    f"Odoo appointment: {appointment.name}<br/>"
                    f"Package: {service.name}<br/>"
                    f"Phone: {phone}"
                ),
            })

            result = {
                "ok": True,
                "reference": appointment.name,
                "total": appointment.total_price,
                "total_formatted": f"TZS {appointment.total_price:,.0f}",
                "date_label": appointment_local.strftime("%A, %d %B %Y"),
                "time_label": appointment_local.strftime("%-I:%M %p"),
            }
            if self._is_ajax():
                return request.make_json_response(result)
            return request.render("stephans_website_theme.booking_success", {"appointment": appointment})
        except (ValidationError, UserError, ValueError) as error:
            request.env.cr.rollback()
            return self._error_response(str(error))
        except Exception:
            request.env.cr.rollback()
            _logger.exception("Could not create website grooming appointment")
            return self._error_response("The booking could not be recorded. Please try again.", status=500)

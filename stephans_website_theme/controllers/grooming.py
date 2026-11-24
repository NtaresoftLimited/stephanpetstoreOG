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
        """
        Accept and normalize mobile / phone numbers worldwide.
        - Local Tanzanian (07..., 06..., 7..., 6...) -> +255...
        - Tanzanian with country code (255...) -> +255...
        - Worldwide international numbers (E.164: +1, +44, +254, +971, etc.) -> +<digits>
        - Leading 00 international prefix -> +<digits>
        """
        if not phone:
            raise ValidationError("Please enter your phone number.")
        compact = re.sub(r"[\s()\-]", "", str(phone).strip())
        digits = re.sub(r"\D", "", compact)
        if not digits:
            raise ValidationError("Please enter a valid phone number.")

        # 00 international dial prefix (e.g., 001..., 00254...)
        if digits.startswith("00") and len(digits) > 8:
            digits = digits[2:]

        # Local Tanzanian 10-digit (07XXXXXXXX, 06XXXXXXXX) or 9-digit (7XXXXXXXX, 6XXXXXXXX)
        if (len(digits) == 10 and digits.startswith("0") and digits[1] in ("6", "7")):
            digits = "255" + digits[1:]
        elif (len(digits) == 9 and digits[0] in ("6", "7")):
            digits = "255" + digits
        elif digits.startswith("255") and len(digits) == 12:
            pass  # Already Tanzanian E.164 digits
        elif len(digits) < 7 or len(digits) > 15:
            raise ValidationError("Please enter a valid phone number (7 to 15 digits with country code).")

        return "+" + digits

    @staticmethod
    def _find_or_track_partner(phone, customer_name, email=None):
        """
        Find existing partner across phone, mobile, and email to avoid duplicates.
        Tracks and detects duplicates in res.partner.
        Returns (partner, is_duplicate, duplicate_partners).
        """
        Partner = request.env["res.partner"].sudo()
        digits = re.sub(r"\D", "", phone)
        last9 = digits[-9:] if len(digits) >= 9 else digits
        last7 = digits[-7:] if len(digits) >= 7 else digits

        phone_fields = ["phone"]
        if "mobile" in Partner._fields:
            phone_fields.append("mobile")

        phone_conditions = []
        for pf in phone_fields:
            phone_conditions.extend([
                (pf, "=", phone),
                (pf, "ilike", last9 if len(last9) >= 7 else digits),
            ])

        or_conds = ["|"] * (len(phone_conditions) - 1) + phone_conditions if len(phone_conditions) > 1 else phone_conditions
        phone_candidates = Partner.search(or_conds + [("active", "=", True), ("id", "!=", 1)], limit=30)

        # Match by digits comparison
        matching = phone_candidates.filtered(
            lambda p: any(re.sub(r"\D", "", getattr(p, f, "") or "").endswith(last7) for f in phone_fields)
        )

        email_matching = Partner.browse()
        if email:
            email_matching = Partner.search([
                ("email", "=ilike", email.strip()),
                ("active", "=", True),
                ("id", "!=", 1),
            ], limit=10)

        all_matches = (matching | email_matching)
        duplicate_partners = all_matches[1:] if len(all_matches) > 1 else Partner.browse()
        is_duplicate = len(all_matches) > 1

        if is_duplicate:
            _logger.info(
                "Duplicate partner records tracked for customer '%s' (%s, %s): %s",
                customer_name, phone, email, all_matches.ids
            )

        if all_matches:
            primary_partner = all_matches.sorted(
                key=lambda p: (-(getattr(p, "customer_rank", 0) or 0), p.id)
            )[0]
            vals = {}
            if not primary_partner.phone:
                vals["phone"] = phone
            if "mobile" in Partner._fields and not primary_partner.mobile:
                vals["mobile"] = phone
            if email and not primary_partner.email:
                vals["email"] = email
            if vals:
                primary_partner.write(vals)
            return primary_partner, is_duplicate, duplicate_partners

        partner_vals = {
            "name": customer_name.strip(),
            "phone": phone,
            "email": email or False,
        }
        if "mobile" in Partner._fields:
            partner_vals["mobile"] = phone
        new_partner = Partner.create(partner_vals)
        return new_partner, False, Partner.browse()

    @staticmethod
    def _is_ajax():
        return request.httprequest.headers.get("X-Requested-With") == "XMLHttpRequest"

    def _error_response(self, message, status=400):
        if self._is_ajax():
            return request.make_json_response({"ok": False, "error": message}, status=status)
        return request.render("stephans_website_theme.booking_error", {"error": message}, status=status)

    @http.route("/grooming", type="http", auth="public", website=True)
    def grooming(self, **kw):
        partner = request.env.user.partner_id if not request.env.user._is_public() else request.env["res.partner"]
        now_local = datetime.now(NAIROBI_TZ)
        detangling_fee = request.env["ir.config_parameter"].sudo().get_float(
            "grooming.detangling_fee", default=100000.0
        )
        return request.render("stephans_website_theme.grooming_page", {
            "valid_times": VALID_TIMES,
            "min_date": now_local.date().isoformat(),
            "default_customer_name": partner.name or "",
            "default_customer_phone": partner.phone or "",
            "default_customer_email": partner.email or "",
            "prices_json": json.dumps(self._get_website_prices()),
            "detangling_fee": detangling_fee,
            "additional_title": "Professional Pet Grooming in Dar es Salaam",
            "meta_description": "Book gentle professional grooming for dogs, cats and small animals at Stephan's Pet Store in Dar es Salaam.",
        })

    @http.route("/grooming/slots", type="http", auth="public", website=True, methods=["GET"], csrf=False)
    def available_slots(self, date=None, branch="masaki", pet_type="dog", pet_category="medium", service_key="standard", **kw):
        """Returns slot availability and scarcity per time slot for a given date and branch."""
        if not date:
            date = datetime.now(NAIROBI_TZ).strftime("%Y-%m-%d")
        branch = branch if branch in ("masaki", "mikocheni") else "masaki"

        # Calculate expected duration based on pet size & package
        duration = 1.0
        if pet_type == "dog":
            if pet_category in ("mini", "small"):
                duration = 1.0 if service_key == "standard" else 1.5
            elif pet_category == "medium":
                duration = 1.5 if service_key == "standard" else 2.0
            elif pet_category == "large":
                duration = 2.0 if service_key == "standard" else 2.5
        elif pet_type in ("cat", "small_animal"):
            duration = 1.0

        Station = request.env["grooming.station"].sudo()
        Appointment = request.env["grooming.appointment"].sudo()

        stations = Station.search([("branch", "=", branch), ("active", "=", True)])
        total_tables = len(stations) or 2

        slot_results = []
        for slot in VALID_TIMES:
            time_val = slot["value"]
            try:
                start_local = datetime.strptime(f"{date} {time_val}", "%Y-%m-%d %H:%M").replace(tzinfo=NAIROBI_TZ)
                end_local = start_local + timedelta(hours=duration)
                start_utc = start_local.astimezone(ZoneInfo("UTC")).replace(tzinfo=None)
                end_utc = end_local.astimezone(ZoneInfo("UTC")).replace(tzinfo=None)

                # Check busy stations during this window
                busy_stations = Appointment.search([
                    ("station_id", "in", stations.ids),
                    ("state", "not in", ("cancelled", "completed")),
                    ("appointment_date", "<", fields.Datetime.to_string(end_utc)),
                    ("appointment_end_date", ">", fields.Datetime.to_string(start_utc)),
                ]).mapped("station_id")

                free_count = total_tables - len(set(busy_stations.ids))

                if free_count <= 0:
                    status = "full"
                    label = f"{slot['label']} (Full)"
                elif free_count == 1:
                    status = "scarce"
                    label = f"{slot['label']} (Only 1 slot left!)"
                else:
                    status = "available"
                    label = slot["label"]

                slot_results.append({
                    "value": time_val,
                    "label": label,
                    "free_slots": max(0, free_count),
                    "status": status,
                    "available": free_count > 0,
                })
            except Exception:
                slot_results.append({
                    "value": time_val,
                    "label": slot["label"],
                    "free_slots": total_tables,
                    "status": "available",
                    "available": True,
                })

        return request.make_json_response({"ok": True, "date": date, "branch": branch, "duration_hours": duration, "slots": slot_results})

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

            phone = self._normalise_phone(post["customer_phone"])
            email = (post.get("customer_email") or "").strip().lower()
            if email and not EMAIL_RE.fullmatch(email):
                raise ValidationError("Enter a valid email address or leave it blank.")

            # Deduplicate and track partner records
            partner, is_dup_partner, dup_partners = self._find_or_track_partner(phone, post["customer_name"], email)

            appointment_utc = appointment_local.astimezone(ZoneInfo("UTC")).replace(tzinfo=None)
            Appointment = request.env["grooming.appointment"].sudo()

            # Check for duplicate appointment (same partner + same pet + same slot)
            existing_booking = Appointment.search([
                ("partner_id", "=", partner.id),
                ("pet_name", "=ilike", post["pet_name"].strip()),
                ("appointment_date", "=", fields.Datetime.to_string(appointment_utc)),
                ("state", "!=", "cancelled"),
            ], limit=1)

            if existing_booking:
                _logger.info("Duplicate grooming appointment detected for partner %s (ID %s): reusing existing booking %s",
                             partner.id, existing_booking.id, existing_booking.name)
                existing_booking.message_post(
                    body=f"🔁 Duplicate booking submission received from website for {post['pet_name'].strip()} on {appointment_local.strftime('%d %b %Y %H:%M')}. Request acknowledged without creating duplicate.",
                    subtype_xmlid="mail.mt_note",
                )
                result = {
                    "ok": True,
                    "reference": existing_booking.name,
                    "total": existing_booking.total_price,
                    "total_formatted": f"TZS {existing_booking.total_price:,.0f}",
                    "date_label": appointment_local.strftime("%A, %d %B %Y"),
                    "time_label": appointment_local.strftime("%-I:%M %p"),
                }
                if self._is_ajax():
                    return request.make_json_response(result)
                return request.render("stephans_website_theme.booking_success", {"appointment": existing_booking})

            branch = (post.get("branch") or "masaki").strip().lower()
            if branch not in ("masaki", "mikocheni"):
                branch = "masaki"

            # Check if all stations at this salon branch are booked for this window
            duration_hours = 1.5
            if pet_type == "dog":
                if pet_category in ("mini", "small"):
                    duration_hours = 1.0 if service_key == "standard" else 1.5
                elif pet_category == "medium":
                    duration_hours = 1.5 if service_key == "standard" else 2.0
                elif pet_category == "large":
                    duration_hours = 2.0 if service_key == "standard" else 2.5
            elif pet_type in ("cat", "small_animal"):
                duration_hours = 1.0

            stop_utc_calc = appointment_utc + timedelta(hours=duration_hours)
            Station = request.env["grooming.station"].sudo()
            branch_stations = Station.search([("branch", "=", branch), ("active", "=", True)])
            if branch_stations:
                busy_stations = Appointment.search([
                    ("station_id", "in", branch_stations.ids),
                    ("state", "not in", ("cancelled", "completed")),
                    ("appointment_date", "<", fields.Datetime.to_string(stop_utc_calc)),
                    ("appointment_end_date", ">", fields.Datetime.to_string(appointment_utc)),
                ]).mapped("station_id")
                if len(set(busy_stations.ids)) >= len(branch_stations):
                    raise ValidationError("All grooming stations at this salon are fully booked for this time. Please choose another slot.")

            service = request.env.ref(SERVICE_XMLIDS[service_key], raise_if_not_found=False)
            if not service:
                raise UserError("The selected grooming package is temporarily unavailable.")
            service = service.sudo()

            det_type = post.get("detangling_type")
            has_det = (det_type in ("moderate", "intensive")) or (post.get("has_detangling") in ("on", "1", "true"))
            raw_notes = (post.get("notes") or "").strip()
            if det_type in ("moderate", "intensive"):
                det_label = "Intensive (+150,000/=)" if det_type == "intensive" else "Moderate (+100,000/=)"
                raw_notes = f"{raw_notes} [Detangling: {det_label}]".strip()

            appointment_values = {
                "partner_id": partner.id,
                "pet_name": post["pet_name"].strip(),
                "pet_type": pet_type,
                "pet_category": pet_category,
                "service_type": "full_grooming",
                "service_id": service.id,
                "branch": branch,
                "appointment_date": fields.Datetime.to_string(appointment_utc),
                "preferred_time": preferred_time,
                "has_detangling": has_det,
                "notes": raw_notes or False,
            }
            if "booking_source" in Appointment._fields:
                appointment_values["booking_source"] = "odoo_website"
            if "website_id" in Appointment._fields:
                website = getattr(request, "website", None) or (request.env["website"].search([], limit=1) if "website" in request.env else None)
                if website:
                    appointment_values["website_id"] = website.id
            appointment = Appointment.create(appointment_values)

            # Track duplicate partners in appointment chatter for staff audit
            if is_dup_partner:
                appointment.message_post(
                    body=f"⚠️ <b>Duplicate Contact Warning</b>: Customer '{partner.name}' shares phone/email with existing partner records (IDs: {dup_partners.ids}). Please review contacts to merge duplicates.",
                    subtype_xmlid="mail.mt_note",
                )

            stop_utc = appointment.appointment_end_date or (appointment_utc + timedelta(hours=2))
            st_name = appointment.station_id.name if appointment.station_id else "Auto-Assigned Table"
            request.env["calendar.event"].sudo().create({
                "name": f"[{st_name}] {appointment.pet_name} — {appointment.name}",
                "start": fields.Datetime.to_string(appointment_utc),
                "stop": fields.Datetime.to_string(stop_utc),
                "partner_ids": [(6, 0, [partner.id])],
                "description": (
                    f"Odoo appointment: {appointment.name}<br/>"
                    f"Station: {st_name}<br/>"
                    f"Branch: {appointment.branch.title()}<br/>"
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

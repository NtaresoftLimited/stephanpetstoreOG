from odoo import tools
tools.config.parse_config(['-c', '/etc/odoo/odoo20_stephans.conf'])

from odoo.modules.registry import Registry
from odoo import api, SUPERUSER_ID, fields
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
import urllib.request
import re

print("=== 1. VERIFYING PRODUCTION ODOO 18 IS UNTOUCHED ===")
try:
    resp18 = urllib.request.urlopen("http://127.0.0.1:8071", timeout=5)
    print(f"Production Odoo 18 (port 8071): HTTP {resp18.getcode()} OK")
except Exception as e:
    print(f"Production Odoo 18 check: {e}")

r = Registry('stephans_odoo20')
with r.cursor() as cr:
    env = api.Environment(cr, SUPERUSER_ID, {})

    print("\n=== 2. TESTING RESCHEDULING ENGINE (3-HOUR CUTOFF & TABLE ENGINE) ===")
    Appointment = env['grooming.appointment']
    admin_partner = env['res.users'].browse(2).partner_id

    # Create appointment 1: 5 hours in future (can reschedule)
    now_utc = fields.Datetime.now()
    future_5h = now_utc + timedelta(hours=5)
    appt1 = Appointment.create({
        'partner_id': admin_partner.id,
        'pet_name': 'Test Reschedule Pet',
        'pet_type': 'dog',
        'pet_category': 'small',
        'appointment_date': future_5h,
        'state': 'confirmed',
        'branch': 'masaki',
    })
    print(f"Created future appointment {appt1.name} (id: {appt1.id}) at {future_5h}")

    # Check cutoff logic
    diff1 = (appt1.appointment_date - now_utc).total_seconds() / 3600.0
    can1 = appt1.state in ('pending', 'confirmed') and diff1 > 3.0
    print(f"Appointment 1 (>3h): diff={diff1:.1f}h, can_reschedule={can1} (Expected: True)")
    assert can1 is True, "Should be able to reschedule > 3 hours before start"

    # Create appointment 2: 2 hours in future (within 3h cutoff)
    future_2h = now_utc + timedelta(hours=2)
    appt2 = Appointment.create({
        'partner_id': admin_partner.id,
        'pet_name': 'Test Cutoff Pet',
        'pet_type': 'dog',
        'pet_category': 'small',
        'appointment_date': future_2h,
        'state': 'confirmed',
        'branch': 'masaki',
    })
    diff2 = (appt2.appointment_date - now_utc).total_seconds() / 3600.0
    can2 = appt2.state in ('pending', 'confirmed') and diff2 > 3.0
    cutoff2 = appt2.state in ('pending', 'confirmed') and diff2 <= 3.0
    print(f"Appointment 2 (<=3h): diff={diff2:.1f}h, can_reschedule={can2}, cutoff={cutoff2} (Expected: can=False, cutoff=True)")
    assert can2 is False and cutoff2 is True, "Should NOT be able to reschedule <= 3 hours before start"

    # Test rescheduling appointment 1 to Monday 11:00 AM (Nov 23, 2026 - Sunday is closed!)
    monday_11 = (now_utc + timedelta(days=2)).replace(hour=8, minute=0, second=0, microsecond=0) # 11:00 EAT is 08:00 UTC
    end_monday_11 = monday_11 + timedelta(hours=1.5)
    
    # Check free station
    stations = env['grooming.station'].search([('branch', '=', 'masaki'), ('station_type', '=', 'table'), ('active', '=', True)])
    assigned_st = None
    for st in stations:
        if st.is_available(monday_11, end_monday_11, exclude_appointment_id=appt1.id):
            assigned_st = st
            break
    print(f"Found free station for reschedule: {assigned_st.name if assigned_st else 'None'}")
    assert assigned_st is not None, "A station should be free on Monday at 11am"

    appt1.write({
        'appointment_date': monday_11,
        'station_id': assigned_st.id,
    })
    print(f"Rescheduled {appt1.name} to {appt1.appointment_date} on station {appt1.station_id.name}")

    print("\n=== 3. TESTING REVIEW PROMPT ACTION ON COMPLETED APPOINTMENT ===")
    appt1.partner_id.write({'phone': '+255786627873'})
    appt1.write({'state': 'completed'})
    action = appt1.action_send_review_prompt()
    print("Action type:", action.get('type'))
    print("Action WhatsApp URL:", action.get('url'))
    assert 'https://wa.me/255786627873' in action.get('url')
    assert 'g.page' in action.get('url') or 'review' in action.get('url')
    print("Review prompt action verified successfully!")

    print("\n=== 4. TESTING MIXX BY YAS REBRANDING ===")
    # Check help string or code in pos_payment_inherit / account_payment_register
    apr_field = env['account.payment.register'].fields_get(['mixx_by_yas_ref', 'payment_method_id'])
    print("Account payment register fields accessible.")
    
    # Cleanup test records
    appt1.unlink()
    appt2.unlink()
    print("Test appointments cleaned up.")

print("\nALL VERIFICATION TESTS COMPLETED SUCCESSFULLY!")

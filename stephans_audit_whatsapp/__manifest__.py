# -*- coding: utf-8 -*-
{
    "name": "Stephans Audit Logs with WhatsApp Notifications",
    "version": "20.0.1.0.0",
    "category": "Extra Tools",
    "summary": "Real-time security and operational audit trail with instant WhatsApp notifications",
    "author": "Stephans Pet Store",
    "license": "LGPL-3",
    "depends": [
        "base",
        "mail",
        "point_of_sale",
        "stock",
        "whatsapp_connector",
    ],
    "data": [
        "security/ir.access.csv",
        "data/default_audit_rules.xml",
        "views/audit_whatsapp_rule_views.xml",
        "views/audit_whatsapp_log_views.xml",
        "views/audit_whatsapp_menus.xml",
    ],
    "installable": True,
    "application": True,
    "auto_install": False,
}

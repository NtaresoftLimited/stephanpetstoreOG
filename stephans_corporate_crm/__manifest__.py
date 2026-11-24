# -*- coding: utf-8 -*-
{
    'name': "Stephan's Corporate Key-Account CRM",
    'version': '20.0.1.0.0',
    'category': 'Sales/CRM',
    'summary': 'Corporate Key-Account CRM with Dynamic Q1, Q2, Q3, Q4 Customer Boxes Logic',
    'description': """
Stephan's Corporate Key-Account CRM
====================================
Advanced Customer Relationship Management tailored for Corporate Key Accounts, B2B clients,
breeders, veterinary clinics, pet boarding facilities, and VIP pet parents.

Key Features:
-------------
* **4-Box Customer Matrix (Q1, Q2, Q3, Q4):**
  - **Q1 (Active Box):** Active customers with sales or groomings within the last 30 days.
  - **Q2 (Slipping Box):** 1 month (31-60 days) with no sales and no groomings. Needs proactive outreach.
  - **Q3 (Dormant Box):** 2-3 months (61-90 days) without activity. High churn risk.
  - **Q4 (Churned Box):** >3 months (>90 days) inactive. Win-back campaign required.

* **Dynamic Shifting Engine:**
  - Automated Nightly Cron shifts accounts across Q1 -> Q2 -> Q3 -> Q4 based on days of inactivity.
  - Real-time Promotion: Immediately moves accounts to Q1 upon sales order confirmation, POS purchase, or grooming appointment completion.
  - Full Audit Trail & Shift Logs (`corporate.crm.shift.log`) tracking every promotion, demotion, trigger, and spend history.

* **Account Manager Alerts & Activities:**
  - Automatically creates scheduled CRM activities for Key Account Managers when an account slips into Q2 or Q3.
  - Integrated WhatsApp Re-engagement wizard with pre-composed messages.

* **Interactive Kanban & Dashboards:**
  - Color-coded Quadrant Kanban view with quick actions (Call, WhatsApp, Schedule Grooming, Create Quote).
  - Health score indicators (0-100), pet registry links, and cohort performance analytics.
  - Direct integration into LuCy Management Console and Sales menus.
    """,
    'author': "Stephan's Pet Store",
    'website': 'https://stephanspetstore.co.tz',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'mail',
        'sale_management',
        'point_of_sale',
        'grooming',
    ],
    'data': [
        'security/corporate_crm_security.xml',
        'security/ir.access.csv',
        'data/crm_stage_data.xml',
        'data/mail_activity_type_data.xml',
        'data/crm_template_data.xml',
        'data/ir_cron.xml',
        'views/crm_stage_views.xml',
        'views/crm_deal_views.xml',
        'views/crm_shift_log_views.xml',
        'views/res_partner_views.xml',
        'views/res_config_settings_views.xml',
        'wizard/reengagement_wizard_views.xml',
        'wizard/lost_wizard_views.xml',
        'views/menu_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'stephans_corporate_crm/static/src/scss/corporate_crm.scss',
        ],
    },
    'application': True,
    'installable': True,
    'auto_install': False,
}

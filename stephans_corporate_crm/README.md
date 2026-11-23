# Stephan's Corporate Key-Account CRM

An enterprise-grade Customer Relationship Management & Pipeline module engineered specifically for **Stephan's Pet Store** (Odoo 20). 

It features an intelligent **4-Quadrant Customer Box Matrix (Q1, Q2, Q3, Q4)**, an automated **Dynamic Shifting Engine**, and a dedicated **Key-Account Deals Pipeline** supporting full CRUD and tailored business cases.

---

## 🏛️ 1. Customer Matrix Logic (Q1, Q2, Q3, Q4)

| Box | Quadrant Name | Inactivity Condition | Strategy & Automation |
| :--- | :--- | :--- | :--- |
| **Q1** | **Active Box** | Active within **≤ 30 days** (Recent sale or grooming) | **VIP Retention:** Dedicated Key Account Manager, automated loyalty status, upselling premium nutrition/grooming packages. |
| **Q2** | **Slipping Box** | **31 - 60 days** without sales AND without groomings | **Proactive Outreach:** Automatically schedules KAM follow-up call activity. Spawns a Retention Deal in the pipeline. 1-click WhatsApp check-in for pets due for 4-week grooming. |
| **Q3** | **Dormant Box** | **61 - 90 days** without sales AND without groomings | **Critical Win-Back:** Urgent KAM task and high-priority retention deal. Generates 10% VIP reactivation voucher outreach. |
| **Q4** | **Churned Box** | **> 90 days** without transactions or never ordered | **Executive Reconnect:** Churn diagnosis, feedback survey, re-acquisition offer. |

---

## 💼 2. Key-Account Pipeline & Business Cases (Full CRUD)

The Deals Pipeline (`corporate.crm.deal`) is specifically designed around Stephan's Pet Store commercial and service operations:

### 🎯 Business Cases Implemented:
1. **New B2B Account Acquisition (`new_b2b`):**
   - Onboarding Veterinary Clinics, Commercial Breeders, Pet Hotels, and Security K9 Units.
   - Captures corporate tax ID (TIN), business registration, credit terms, and pricing tier (Platinum, Gold, Silver).
2. **Grooming Fleet / Service Contract SLA (`grooming_fleet`):**
   - Recurring service contracts for corporate pet fleets (e.g., 10 working dogs groomed every 2 weeks).
   - Tracks pet fleet count, grooming frequency, and preferred salon branch (Masaki, Mikocheni).
   - "Schedule Grooming" button creates linked `grooming.appointment` records.
3. **Monthly Food & Supplies Replenishment SLA (`replenishment_sla`):**
   - Standing orders for wholesale pet food (Royal Canin, Bioline, Josera, etc.) and medical supplies.
   - Tracks replenishment cycle (Weekly, Bi-weekly, Monthly) and doorstep delivery logistics.
   - "New Quotation" button generates pre-linked `sale.order` quotations.
4. **Q2 Slipping Win-Back Pipeline (`q2_recovery`):**
   - Automatically triggered when an active account slips past 30 days without activity.
   - Assigned to Key Account Manager with pre-filled WhatsApp check-in.
5. **Q3 Dormant Account Recovery (`q3_recovery`):**
   - Critical churn prevention deal with 10% VIP incentive proposal.
6. **Q4 Churned Re-acquisition (`q4_churn_recovery`):**
   - Re-acquisition campaigns with structured lost reasons analysis.

### 🔄 Full CRUD Features:
- **Create:** 
  - Quick-create cards directly in the Kanban view.
  - Detailed form creation with SLA parameters.
  - Automatic creation from customer box demotions (Q2/Q3).
- **Read:**
  - Drag-and-drop Kanban view grouped by Stage with column totals (Sum of Expected Contract Value & Monthly Recurring Revenue).
  - List / Tree view with priority stars, progress bars, and box status badges.
  - Interactive Form view with ribbons ("Won", "Lost"), smart buttons, and chatter.
  - Pivot analysis (Deal Type × Stage × KAM Revenue).
  - Graph funnel analytics.
  - Calendar view for closing deadlines and contract renewal dates.
- **Update:**
  - Drag-and-drop across stages in Kanban.
  - "Mark as Won" button: sets probability to 100%, writes contract renewal date to the customer profile, and promotes the customer to **Q1 Active**.
  - "Mark as Lost" button: opens wizard to record structured lost reason and churn feedback.
  - Inline list editing.
- **Delete & Archive:**
  - Active archive toggle (`active`) and record deletion permissions managed by security groups.

---

## ⚡ 3. Dynamic Shifting Engine

1. **Instant Promotion (Jumping to Q1):**
   - Sales Order confirmation (`action_confirm`).
   - POS transaction payment (`pos.order`).
   - Grooming appointment booking or completion (`grooming.appointment`).
   - Marking a Pipeline Deal as Won (`action_set_won`).
2. **Automated Demotion (Nightly Scheduled Action):**
   - Cron Job runs daily to evaluate inactivity days across all accounts.
   - Automatically shifts accounts across boxes (Q1 ➔ Q2 ➔ Q3 ➔ Q4).
   - Logs every shift in `corporate.crm.shift.log`.
   - Schedules KAM activities and spawns pipeline retention deals.

---

## 📱 4. One-Click WhatsApp & Re-engagement Wizard

Key Account Managers can launch direct WhatsApp outreach from:
- The Customer Kanban card
- The Customer Form view
- The Pipeline Deal card or form view

Auto-formats Tanzania phone numbers (`+255...`) and dynamically fills pet names from `grooming.pet`.

---

## 📊 5. Navigation & Access

- **Top-Level App:** `Key Account CRM`
  - `Deals Pipeline` (Kanban, List, Form, Pivot, Graph, Calendar)
  - `Customer Boxes (Q1 - Q4)` (4-Quadrant Matrix)
  - `Accounts` ➔ `Corporate Key Accounts`
  - `Box Shifts & Retention` ➔ `Box Shift Audit Trail`
  - `Configuration` ➔ `Settings`, `Pipeline Stages`, `Lost Reasons`
- **LuCy Console Integration:** Integrated under `LuCy` ➔ `Key Account CRM`.
- **Sales App Integration:** Integrated under `Sales` ➔ `Orders` ➔ `Key Account Pipeline` & `Key Account Boxes`.

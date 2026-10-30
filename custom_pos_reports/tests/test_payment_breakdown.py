from odoo.tests.common import TransactionCase


class TestPaymentBreakdown(TransactionCase):

    def test_split_pos_payment_excludes_only_unpaid_customer_balance(self):
        payments, by_location, cash_received = self.env[
            'pos.details.wizard'
        ]._summarize_payment_rows([
            {
                'method': 'Cash (Sinza)',
                'amount': 950000.0,
                'location': 'TechOvers Sinza',
                'is_customer_account': False,
                'is_cash': True,
            },
            {
                'method': 'Lipa CRDB (Sinza)',
                'amount': 500000.0,
                'location': 'TechOvers Sinza',
                'is_customer_account': False,
                'is_cash': False,
            },
            {
                'method': 'Customer Account (Sinza)',
                'amount': 500000.0,
                'location': 'TechOvers Sinza',
                'is_customer_account': True,
                'is_cash': False,
            },
        ])

        self.assertEqual(sum(payments.values()), 1450000.0)
        self.assertNotIn('Customer Account (Sinza)', payments)
        self.assertEqual(cash_received, 950000.0)
        self.assertEqual(
            by_location['Lipa CRDB (Sinza)']['TechOvers Sinza'], 500000.0)

    def test_customer_account_is_replaced_by_real_invoice_receipts(self):
        payments, by_location, cash_received = self.env[
            'pos.details.wizard'
        ]._summarize_payment_rows([
            {
                'method': 'Customer Account (Sinza)',
                'amount': 1950000.0,
                'location': 'TechOvers Sinza',
                'is_customer_account': True,
                'is_cash': False,
            },
            {
                'method': 'Cash (Sinza)',
                'amount': 975000.0,
                'location': 'TechOvers Sinza',
                'is_customer_account': False,
                'is_cash': True,
            },
            {
                'method': 'Lipa CRDB (Sinza)',
                'amount': 475000.0,
                'location': 'TechOvers Sinza',
                'is_customer_account': False,
                'is_cash': False,
            },
            {
                'method': 'NMB Sinza',
                'amount': 500000.0,
                'location': 'TechOvers Sinza',
                'is_customer_account': False,
                'is_cash': False,
            },
        ])

        self.assertNotIn('Customer Account (Sinza)', payments)
        self.assertEqual(sum(payments.values()), 1950000.0)
        self.assertEqual(payments['Cash (Sinza)'], 975000.0)
        self.assertEqual(payments['Lipa CRDB (Sinza)'], 475000.0)
        self.assertEqual(payments['NMB Sinza'], 500000.0)
        self.assertEqual(cash_received, 975000.0)
        self.assertEqual(
            by_location['Cash (Sinza)']['TechOvers Sinza'], 975000.0)

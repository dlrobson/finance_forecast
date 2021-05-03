import unittest

from saving_vessels import TFSA, RRSP, EmergencyFund, NonRegisteredAccount
from expenses import Taxes, Mortgage, LivingExpenses, DEFAULT_CHILD_COSTS

BASIC_AMOUNT = 1000
BRACKETS = [BASIC_AMOUNT, 11000, 111000]
TAX_RATES = [0.1, 0.2, 0.3]


class TestSavingMethods(unittest.TestCase):
    def test_tax_check(self):
        federal_tax = Taxes(BRACKETS, TAX_RATES, BASIC_AMOUNT)
        self.assertEqual(federal_tax.tax_payable(-1000), 0)
        self.assertEqual(federal_tax.tax_payable(0), 0)
        self.assertEqual(federal_tax.tax_payable(1000), 0)
        self.assertEqual(federal_tax.tax_payable(11000), 1000)
        self.assertEqual(federal_tax.tax_payable(111000), 21000)

    def test_tax_increment(self):
        federal_tax = Taxes(BRACKETS, TAX_RATES, BASIC_AMOUNT)
        federal_tax.increment_values(0.01)
        self.assertEqual(federal_tax.brackets()[0], 1000 * 1.01)
        self.assertEqual(federal_tax.brackets()[1], 11000 * 1.01)
        self.assertEqual(federal_tax.brackets()[2], 111000 * 1.01)

    def test_tfsa(self):
        tfsa_account = TFSA(1000, 10000)
        self.assertEqual(tfsa_account.balance, 1000)
        self.assertEqual(tfsa_account.contribution_room, 10000)

        self.assertEqual(tfsa_account.withdraw(2000), 1000)
        self.assertEqual(tfsa_account.balance, 0)
        self.assertEqual(tfsa_account.contribution_room, 10000)

        self.assertEqual(tfsa_account.deposit(20000), 10000)
        self.assertEqual(tfsa_account.balance, 10000)
        self.assertEqual(tfsa_account.contribution_room, 0)

        tfsa_account.increment_year(5000, 1.00)
        self.assertEqual(tfsa_account.balance, 10000 * 2)
        self.assertEqual(tfsa_account.contribution_room, 1000 + 5000)

    def test_rrsp(self):
        rrsp_account = RRSP(1000, 10000)
        self.assertEqual(rrsp_account.balance, 1000)
        self.assertEqual(rrsp_account.contribution_room, 10000)

        self.assertEqual(rrsp_account.withdraw(2000), 1000)
        self.assertEqual(rrsp_account.balance, 0)
        self.assertEqual(rrsp_account.contribution_room, 10000)

        self.assertEqual(rrsp_account.deposit(20000), 10000)
        self.assertEqual(rrsp_account.balance, 10000)
        self.assertEqual(rrsp_account.contribution_room, 0)

        # Room only increases by 100
        rrsp_account.increment_year(1800, 1.00)
        self.assertEqual(rrsp_account.balance, 10000 * 2)
        self.assertEqual(rrsp_account.contribution_room, 1800 * 0.18)

    def test_emergency_fund(self):
        emergency_fund = EmergencyFund(0, 6)
        self.assertEqual(emergency_fund.balance, 0)
        self.assertEqual(emergency_fund.emergency_months, 6)
        self.assertEqual(emergency_fund.amount_over_limit(1000), -6000)

        emergency_fund.deposit(8000)
        self.assertEqual(emergency_fund.balance, 8000)
        self.assertEqual(emergency_fund.amount_over_limit(1000), 2000)

        emergency_fund.withdraw(2000)
        self.assertEqual(emergency_fund.balance, 6000)
        self.assertEqual(emergency_fund.amount_over_limit(1000), 0)

    def test_non_reg_account(self):
        non_reg_account = NonRegisteredAccount()

        # Buy 10000 worth of shares
        non_reg_account.deposit(10000)
        self.assertEqual(non_reg_account.balance, 10000)

        self.assertEqual(non_reg_account.withdraw(9000)[1], 0)
        self.assertEqual(non_reg_account.balance, 1000)

        non_reg_account.deposit(9000)

        # Shares doubled in value
        non_reg_account.increment_n_years(1, 1.00)
        self.assertEqual(non_reg_account.balance, 20000)
        self.assertEqual(non_reg_account.withdraw(20000)[1], 10000 / 2)

        # Empty account again. Repeat double in value
        non_reg_account.deposit(5000)
        non_reg_account.increment_n_years(1, 1.00)
        non_reg_account.deposit(10000)
        self.assertEqual(non_reg_account.balance, 20000)
        non_reg_account.increment_n_years(1, 1.00)
        self.assertEqual(non_reg_account.balance, 40000)
        expected_capital_gains = (40000 - 15000) * (10000 / 40000)
        self.assertEqual(
            non_reg_account.withdraw(10000)[1], 0.5 * expected_capital_gains
        )
        expected_capital_gains = (30000 - 15000 * (40000 - 10000) / 40000) * (
            30000 / 30000
        )
        self.assertEqual(
            non_reg_account.withdraw(30000)[1], 0.5 * expected_capital_gains
        )


class TestExpenseMethods(unittest.TestCase):
    def test_mortgage_basics(self):
        mortgage = Mortgage(120000, 20000, 0.1, 20)
        self.assertTrue(abs(mortgage.monthly_payment - 965) < 1)
        self.assertEqual(mortgage.principal_remaining, 100000)
        self.assertEqual(mortgage.interest_paid, 0)
        self.assertEqual(mortgage.expected_payoff_months(), 240)

        # Iterate to next month. Expect to have about 99868 principal remaining
        # and 833.33 in interest
        mortgage.iterate_n_months(1)
        self.assertTrue(abs(mortgage.principal_remaining - 99868) < 1)
        self.assertTrue(abs(mortgage.interest_paid - 833.33) < 1)

        # Multiple months. 6 Total now
        mortgage.iterate_n_months(5)
        self.assertTrue(abs(mortgage.principal_remaining - 99193) < 1)

        # Attempt a one time additional payment
        mortgage.additional_payment(20000)
        self.assertTrue(abs(mortgage.principal_remaining - 79193) < 1)

        # Iterate to the next month. 7 Total now
        mortgage.iterate_n_months(1)
        self.assertTrue(abs(mortgage.principal_remaining - 78888) < 1)

    def test_mortgage_accelerated_payments(self):
        mortgage = Mortgage(120000, 20000, 0.1, 20)
        self.assertTrue(abs(mortgage.monthly_payment - 965) < 1)
        self.assertEqual(mortgage.principal_remaining, 100000)

        mortgage.additional_payment(20000)
        self.assertEqual(mortgage.principal_remaining, 80000)

        mortgage.iterate_n_months(6)
        self.assertTrue(abs(mortgage.principal_remaining - 78172) < 1)

        mortgage.additional_payment(20000)
        self.assertTrue(abs(mortgage.principal_remaining - 58172) < 1)
        self.assertEqual(mortgage.expected_payoff_months(), 91 - 6)

    def test_expense_class(self):
        # Living costs of 2000/month and Rent of 1000/month
        living_expenses = LivingExpenses(2000, 1000)
        self.assertEqual(living_expenses.living_costs, 2000)
        self.assertEqual(living_expenses.rent, 1000)

        living_expenses.living_costs = 3000
        living_expenses.rent = 500
        self.assertEqual(living_expenses.living_costs, 3000)
        self.assertEqual(living_expenses.rent, 500)
        self.assertEqual(living_expenses.monthly_living_costs(include_rent=True), 3500)
        self.assertEqual(living_expenses.monthly_living_costs(include_rent=False), 3000)

        living_expenses.add_child()
        self.assertEqual(
            living_expenses.monthly_living_costs(include_rent=True),
            3500 + DEFAULT_CHILD_COSTS[0],
        )

        living_expenses.increment_year()
        self.assertEqual(
            living_expenses.monthly_living_costs(include_rent=True),
            3500 + DEFAULT_CHILD_COSTS[1],
        )
        living_expenses.add_child()
        self.assertEqual(
            living_expenses.monthly_living_costs(include_rent=True),
            3500 + DEFAULT_CHILD_COSTS[0] + DEFAULT_CHILD_COSTS[1],
        )

        living_expenses.increment_year()
        self.assertEqual(
            living_expenses.monthly_living_costs(include_rent=True),
            3500 + DEFAULT_CHILD_COSTS[1] + DEFAULT_CHILD_COSTS[2],
        )


if __name__ == "__main__":
    unittest.main()

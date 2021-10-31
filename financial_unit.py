#!/usr/bin/env python3
from typing import List

from expenses import (
    Expense,
    LivingExpenses,
    Mortgage,
    tax_payable,
    ei_contribution,
    cpp_contribution,
)
from saving_vessels import rrsp_before_tax_calc
from person import Person


class BalanceTracker:
    def __init__(self) -> None:
        self._tfsa_balance = []
        self._emergency_fund = []
        self._rrsp_balance = []
        self._nra_balance = []
        self._mortgage_principal = []
        self._years = []

    def prepare_next_iteration(self, year: int) -> None:
        self._tfsa_balance.append(0)
        self._emergency_fund.append(0)
        self._years.append(year)
        self._rrsp_balance.append(0)
        self._nra_balance.append(0)
        self._mortgage_principal.append(0)


class FinancialUnit:
    def __init__(
        self, init_year: int, persons: List[Person], living_expenses: LivingExpenses
    ) -> None:
        self._persons = persons
        self._living_expenses = living_expenses
        self._year = init_year

    class Settings:
        pay_house_down_asap = True

    _settings = Settings()

    @property
    def settings(self) -> Settings:
        return self._settings

    @settings.setter
    def settings(self, new_settings: Settings) -> None:
        self._settings = new_settings

    class MortgageGoal:

        _active = False

        def __init__(self, mortgage_info: Mortgage) -> None:
            self.mortgage = mortgage_info

        def is_active(self) -> bool:
            return self._active

        def set_active(self, set_to_active=True) -> None:
            self._active = set_to_active

    _mortgage_goal = None
    _balance_tracker = BalanceTracker()
    _expenses = []
    _children = []

    def add_one_time_payment(self, payment_amount: float, year_paid: int) -> None:
        self._expenses.append(Expense(payment_amount, year_paid))

    def add_recurring_cost(
        self,
        payment_amount: float,
        year_first_payment: int,
        period_n_years: int = 1,
    ) -> None:
        self._expenses.append(
            Expense(payment_amount, year_first_payment, period_n_years)
        )

    def new_child(self, year_have_child: float) -> None:

        if year_have_child < self._year:
            return

        self._children.append(year_have_child)

    def __annual_living_expenses(self) -> None:

        total_expenses = 0

        # Add child expense
        for year_have_child in self._children:
            if year_have_child == self._year:
                self._living_expenses.add_child()

        # Determines living and rent/mortgage costs
        if self._mortgage_goal is not None and self._mortgage_goal.is_active():
            if not self._mortgage_goal.mortgage.is_house_paid():
                total_expenses += self._mortgage_goal.mortgage.expected_n_cost(12)

            total_expenses += self._living_expenses.increment_year(False)

        else:
            total_expenses += self._living_expenses.increment_year(True)

        # Calculates any additional expenses
        for expense in self._expenses:
            total_expenses += expense.year_cost(self._year)

        return total_expenses

    def house_purchase(self, mortgage: Mortgage) -> None:
        # Stores the Mortgage information
        self._mortgage_goal = self.MortgageGoal(mortgage)

    def __withdrawable_cash(self, after_tax_calc: bool = True) -> tuple:

        withdrawable_cash = []
        sum = 0

        for person in self._persons:

            withdrawable = person.withdrawable_cash(after_tax_calc)

            withdrawable_cash.append(withdrawable)
            sum += withdrawable

        return withdrawable_cash, sum

    def __withdraw_cash(self, amount: float, after_tax_calc: bool = True) -> float:

        withdrawable_cash, sum = self.__withdrawable_cash(after_tax_calc)

        # If we don't have enough money, we return early.
        if sum < amount:
            return 0

        # Withdraws the same ratio of withdrawable cash from each person
        ratio = amount / sum
        for i in range(len(self._persons)):
            cash = withdrawable_cash[i]
            withdraw_amount = cash * ratio
            self._persons[i].withdraw_cash(withdraw_amount)

        return amount

    def __purchase_house(self) -> bool:

        # If the mortgage is already active, return
        if self._mortgage_goal.is_active():
            return False

        # Now attempt to withdraw enough cash for the down payment
        amount_withdrawn = self.__withdraw_cash(
            self._mortgage_goal.mortgage.down_payment
        )

        # We didn't withdraw anything. Return
        if amount_withdrawn == 0:
            return False

        # We withdrew money for the house. Set the mortgage as active
        self._mortgage_goal.set_active()
        return True

    def increment_n_years(self, n: int) -> None:
        for _ in range(n):
            self._balance_tracker.prepare_next_iteration(self._year)

            for person_i in range(len(self._persons)):

                self.__calculate_person_contribution(person_i)

                # Iterate to next year
                self._persons[person_i]._yearly_investment_taxable_income = 0
                self._persons[person_i]._salary *= (
                    1 + self._persons[person_i]._settings.annual_salary_increase
                )
                self._persons[person_i]._tfsa.increment_year(
                    self._persons[person_i]._settings.index_fund_return
                )
                # Utilizes next year salary
                self._persons[person_i]._rrsp.increment_year(
                    self._persons[person_i]._salary,
                    self._persons[person_i]._settings.index_fund_return,
                )
                self._persons[person_i]._nra.increment_year(
                    self._persons[person_i]._settings.index_fund_return
                )

                if (
                    self._persons[person_i]._age
                    == self._persons[person_i]._settings.retirement_age
                ):
                    self._persons[person_i]._salary = 0

                self._persons[person_i]._age += 1

                self._balance_tracker._emergency_fund[-1] += self._persons[
                    person_i
                ]._emergency_fund.balance
                # Update balance tracker with new values
                self._balance_tracker._tfsa_balance[-1] += self._persons[
                    person_i
                ]._tfsa.balance
                self._balance_tracker._rrsp_balance[-1] += self._persons[
                    person_i
                ]._rrsp.balance
                self._balance_tracker._nra_balance[-1] += self._persons[
                    person_i
                ]._nra.balance

            if self._mortgage_goal is not None:
                if self._mortgage_goal.is_active():
                    self._balance_tracker._mortgage_principal[-1] = (
                        self._mortgage_goal.mortgage._house_cost
                        - self._mortgage_goal.mortgage.principal_remaining
                    )

                    self._mortgage_goal.mortgage.iterate_n_months(12)
                else:
                    self._balance_tracker._mortgage_principal[-1] = 0

            self._year += 1

    def __calculate_person_contribution(self, person_i: int) -> None:
        """Steps:
        1.  First build emergency fund
        2.  Contribute TFSA
        3.  Contribute NRA until house is purchased
        4.  Contribute TFSA and RRSP afterwards, ~15% per year total
            - Any extra cash goes towards mortgage if pay_house_down_asap is True
        5.  Once mortgage is paid off, contribute additional money to
            TFSA > RRSP > NRA

        """
        withdrawn_cash = 0

        if self._mortgage_goal is not None:
            # Attempt to buy the house if the house has not already been purchased
            if not self._mortgage_goal.is_active():
                purchased_house = self.__purchase_house()

            # If we purchased the house, we should empty out our NRA accounts to pay
            # down the house early. The else-statement prevents us from withdrawing the
            # same year that the house was purchased, reducing the amount of capital
            # gains to pay.
            else:
                withdrawn_cash = self._persons[person_i].withdraw_cash(
                    self._persons[person_i].withdrawable_cash(
                        after_tax_calc=False, include_retirement=False
                    )
                )

        # net_positive will hold how much money we have left after taxes and expenses.
        # Initialize the value to negative so we can run through the while loop the
        # first time, mimicing a do-while loop
        net_positive = -1
        while net_positive < 0:
            bt_income = (
                self._persons[person_i]._salary
                + self._persons[person_i]._yearly_investment_taxable_income
            )

            ei_amount = ei_contribution(bt_income)
            cpp_amount = cpp_contribution(bt_income)
            tax = tax_payable(bt_income)
            at_income = bt_income - tax - ei_amount - cpp_amount

            # Divide the expenses between persons
            living_expenses = self.__annual_living_expenses() / len(self._persons)
            net_positive = at_income + withdrawn_cash - living_expenses

            # If this number is negative, then we need to withdraw money
            if net_positive < 0:
                withdrawn_cash += self._persons[person_i].withdraw_cash(-net_positive)

        remaining_contribution_retirement = (
            self._persons[person_i]._settings.max_retirement_contribution * at_income
        )

        # Emergency Fund
        remaining_balance = self.__emergency_fund_contribution(person_i, net_positive)

        # TFSA
        (
            remaining_contribution_retirement,
            remaining_balance,
        ) = self.__tfsa_contribution(
            person_i, remaining_contribution_retirement, remaining_balance
        )

        # RRSP
        remaining_balance = self.__rrsp_contribution(
            person_i,
            remaining_contribution_retirement,
            remaining_balance,
            bt_income,
            at_income,
        )

        # DOWN PAYMENT / NRA
        # Any remaining money gets contributed to the house, and anything remaining is
        # placed within in the non-registered account.
        if (
            self._settings.pay_house_down_asap
            and self._mortgage_goal is not None
            and self._mortgage_goal.is_active()
            and not self._mortgage_goal.mortgage.is_house_paid()
        ):
            additional_payment = self._mortgage_goal.mortgage.additional_payment(
                remaining_balance
            )
            remaining_balance -= additional_payment

        self._persons[person_i]._nra.deposit(remaining_balance)

    def __emergency_fund_contribution(
        self, person_i: int, net_positive: float
    ) -> float:

        monthly_expenses = self.__annual_living_expenses() / 12
        per_person_monthly_expenses = monthly_expenses / len(self._persons)
        required_contribution = self._persons[
            person_i
        ]._emergency_fund.amount_under_limit(per_person_monthly_expenses)

        if required_contribution > 0:
            emergency_fund_deposit = min(required_contribution, net_positive)
            self._persons[person_i]._emergency_fund.deposit(emergency_fund_deposit)
            remaining_balance = net_positive - emergency_fund_deposit
        else:
            emergency_fund_withdrawal = -required_contribution
            self._persons[person_i]._emergency_fund.withdraw(emergency_fund_withdrawal)
            remaining_balance = net_positive + emergency_fund_withdrawal

        return remaining_balance

    def __tfsa_contribution(
        self,
        person_i: int,
        remaining_contribution_retirement: float,
        remaining_balance: float,
    ) -> tuple:

        # Second, deposit into the TFSA account. We need to make sure we contribute the
        # required remaining retirement portion. If we currently have a mortgage, we
        # will attempt to reduce how much we contribute to the TFSA. However, if the
        # allow_tfsa_withdrawal flag is active, then we will maximize the tfsa regardless
        tfsa_retirement_amount = (
            self._persons[person_i]._tfsa.balance
            * self._persons[person_i]._tfsa_retirement_portion
        )
        if (
            self._mortgage_goal is not None
            and not self._mortgage_goal.mortgage.is_house_paid()
            and not self._persons[person_i]._settings.allow_tfsa_withdrawal
        ):
            # Either we can deposite the contribution room, the amount we need to deposit,
            # or the amount of money we have left to deposit.
            amount_deposited = min(
                self._persons[person_i]._tfsa.contribution_room,
                remaining_contribution_retirement,
                remaining_balance,
            )

            self._persons[person_i]._tfsa.deposit(amount_deposited)
            added_tfsa_retirement_portion = amount_deposited
        else:

            amount_deposited = self._persons[person_i]._tfsa.deposit(remaining_balance)

            added_tfsa_retirement_portion = min(
                amount_deposited, remaining_contribution_retirement
            )

        remaining_balance -= amount_deposited

        tfsa_retirement_amount += added_tfsa_retirement_portion
        remaining_contribution_retirement -= added_tfsa_retirement_portion

        # Convert some of the non-retirement portion to retirement if we have a remaining
        # retirement balance. The case that this covers is when we still need to
        # contribute some money to retirement, but we have a mix of retirement cash and
        # regular cash in the TFSA. This does not change the balance in the account,
        # but instead increases the amount of retirement money in the account.
        retirement_conversion_amount = max(
            0,
            min(
                remaining_contribution_retirement,
                self._persons[person_i]._tfsa.balance - tfsa_retirement_amount,
            ),
        )
        tfsa_retirement_amount += retirement_conversion_amount
        remaining_contribution_retirement -= retirement_conversion_amount

        # Adjust the retirement amount in the tfsa account
        if self._persons[person_i]._tfsa.balance == 0:
            self._persons[person_i]._tfsa_retirement_portion = 0
        else:
            self._persons[person_i]._tfsa_retirement_portion = (
                tfsa_retirement_amount / self._persons[person_i]._tfsa.balance
            )

        return remaining_contribution_retirement, remaining_balance

    def __rrsp_contribution(
        self,
        person_i: int,
        remaining_contribution_retirement: float,
        remaining_balance: float,
        bt_income: float,
        at_income: float,
    ) -> float:
        # Now, check the RRSP. If we have additional money max out the required
        # contribution for retirement. Then, pay additional to the house.
        if (
            remaining_contribution_retirement > 0.1
            or self._mortgage_goal is not None
            and not self._mortgage_goal.mortgage.is_house_paid()
        ):

            # At most, we can contribute either remaining_contribution_retirement,
            # contribution_room, or our remaining amount of money
            RRSP_AT_contribution = min(
                self._persons[person_i]._rrsp.contribution_room,
                remaining_contribution_retirement,
                remaining_balance,
            )
        else:
            RRSP_AT_contribution = min(
                self._persons[person_i]._rrsp.contribution_room,
                remaining_balance,
            )
        # We need to calculate the beforetax contribution. The aftertax contribution we
        # have should be reduced by the after tax contribution

        max_BT_contribution = rrsp_before_tax_calc(
            RRSP_AT_contribution, at_income, bt_income
        )

        BT_contributed = self._persons[person_i]._rrsp.deposit(
            bt_income - max_BT_contribution
        )

        # Case if we don't deposit all of the money in the account
        if abs(BT_contributed - max_BT_contribution) < 0.1:
            extra_AT_money = tax_payable(bt_income - max_BT_contribution) - tax_payable(
                bt_income - BT_contributed
            )
            remaining_contribution_retirement += extra_AT_money
            remaining_balance += extra_AT_money

        remaining_contribution_retirement -= RRSP_AT_contribution
        remaining_balance -= RRSP_AT_contribution

        return remaining_balance

    @property
    def persons(self) -> Person:
        return self._persons

from saving_vessels import TFSA, RRSP, EmergencyFund, NonRegisteredAccount
from expenses import Taxes, Mortgage, LivingExpenses, DEFAULT_CHILD_COSTS

# TODO:
# - Financial goals
#   - Retirement + Retirement Age
#   - Nest Egg goal
#   - HBP ?
# - Settings to tick
#   - Max RRSP/TFSA before house, or after house
#   - Max TFSA before saving for house
#
# Employer RRSP matching
# Add two person functionality
# Keep track of tax avoided by using RRSP, and add RRIF when 71
# Max allowed to contribute to mortgage

INDEX_RETURN = 0.07
TFSA_YEARLY_ROOM_INCREASE = 6000

FEDERAL_BASIC_AMOUNT = 13229
FEDERAL_BRACKETS = [FEDERAL_BASIC_AMOUNT, 48535, 97070, 150474, 214368]
FEDERAL_TAX_RATES = [0.1500, 0.2050, 0.2600, 0.2900, 0.3300]

ONTARIO_BASIC_AMOUNT = 10783
ONTARIO_BRACKETS = [ONTARIO_BASIC_AMOUNT, 44740, 89482, 150000, 220000]
ONTARIO_TAX_RATES = [0.0505, 0.0915, 0.1116, 0.1216, 0.1316]

federal_tax = Taxes(FEDERAL_BRACKETS, FEDERAL_TAX_RATES)
ontario_tax = Taxes(ONTARIO_BRACKETS, ONTARIO_TAX_RATES)


def tax_payable(income: float) -> float:
    return federal_tax.tax_payable(income) + ontario_tax.tax_payable(income)


def rrsp_before_tax_calc(
    AT_deduction: float, AT_original: float, BT_original: float
) -> float:
    # We need to iteratively find the amount of before tax income where the
    # difference with the original and solved after tax income is the after
    # tax deduction.
    BT_guess = BT_original
    AT_guess = BT_original - tax_payable(BT_guess)
    while abs(abs(AT_original - AT_guess) - AT_deduction) > 0.1:

        diff = abs(AT_original - AT_guess) - AT_deduction
        BT_guess += diff
        AT_guess = BT_guess - tax_payable(BT_guess)

    return BT_guess


class Person:
    class MortgageGoal:

        _active = False

        def __init__(self, mortgage_info: Mortgage) -> None:
            self.mortgage = mortgage_info

        def is_active(self) -> bool:
            return self._active

        def set_active(self, set_to_active=True) -> None:
            self._active = set_to_active

    class Expense:
        def __init__(
            self, amount: float, initial_age: int, recurrance: int = 0
        ) -> None:
            self._amount = amount
            self._initial_age = initial_age
            self._recurrance = recurrance

        def year_cost(self, age: int) -> float:
            if self._initial_age == age:
                return amount

            if self._recurrance == 0:
                return 0

            return (
                self._amount if (age - self._initial_age) % self._recurrance == 0 else 0
            )

    class Settings:
        max_tfsa_asap = True
        max_retirement_contribution = 0.15
        annual_salary_increase = 0.03
        retirement_age = 65
        index_fund_return = INDEX_RETURN

    _settings = Settings()
    _mortgage_goal = None
    _expenses = []
    _children = []
    _tfsa_retirement_portion = 0
    _yearly_capital_gains_income = 0

    @property
    def settings(self) -> Settings:
        return self._settings

    @settings.setter
    def settings(self, new_settings: Settings) -> None:
        self._settings = new_settings

    @property
    def tfsa_retirement_portion(self) -> float:
        return self._tfsa_retirement_portion

    @tfsa_retirement_portion.setter
    def tfsa_retirement_portion(self, new_tfsa_retirement_portion: float) -> None:
        self._tfsa_retirement_portion = new_tfsa_retirement_portion

    def __init__(
        self,
        age: int,
        living_expenses: LivingExpenses,
        yearly_salary_BT: float,
        tfsa: TFSA,
        rrsp: RRSP,
        taxable_account: NonRegisteredAccount,
        emergency_fund: EmergencyFund,
    ) -> None:
        self._salary = yearly_salary_BT
        self._age = age
        self._living_expenses = living_expenses
        self._tfsa = tfsa
        self._rrsp = rrsp
        self._nra = taxable_account
        self._emergency_fund = emergency_fund

    def add_one_time_payment(self, payment_amount: float, age_paid: int) -> None:
        self._expenses.append(Expense(payment_amount, age_paid))

    def add_recurring_cost(
        self,
        payment_amount: float,
        age_first_payment: int,
        period_n_years: int = 1,
    ) -> None:
        self._expenses.append(Expense(payment_amount, age_paid, period_n_years))

    def new_child(self, age_have_child: float) -> None:

        if age_have_child < self._age:
            return

        self._children.append(age_have_child)

    def house_purchase(self, mortgage: Mortgage) -> None:
        # Stores the Mortgage information
        self._mortgage_goal = self.MortgageGoal(mortgage)

    def __withdrawable_cash(self) -> float:

        withdrawable_cash = 0

        if not self._settings.max_tfsa_asap:
            withdrawable_cash += self._tfsa.balance * (
                1 - self._tfsa_retirement_portion
            )

        # This is the tax payable if the NRA account is emptied.
        additional_tax_payable = tax_payable(
            self._salary + self._nra.capital_gains(self._nra.balance)
        ) - tax_payable(self._salary)

        withdrawable_cash += self._nra._balance - additional_tax_payable

        return withdrawable_cash

    def __withdraw_cash(self, amount: float) -> float:

        # withdraw 0 if the requested amount is greater than the maximum allowed
        if amount > self.__withdrawable_cash():
            return 0

        # Manage NRA account withdrawals
        total_withdrawn, capital_gains = self._nra.withdraw(amount)
        self._yearly_capital_gains_income += capital_gains

        remaining_withdraw = amount - total_withdrawn

        # Manage TFSA account withdrawals
        self._tfsa_retirement_portion = (
            self._tfsa.balance * self._tfsa_retirement_portion
        ) / (self._tfsa.balance - remaining_withdraw)

        total_withdrawn += self._tfsa.withdraw(remaining_withdraw)

        return total_withdrawn

    def __purchase_house(self) -> bool:
        # Pay for the house down payment, and set the mortgage as active
        if (
            self._mortgage_goal.is_active() is False
            and self.__withdrawable_cash() > self._mortgage_goal.mortgage.down_payment
        ):
            self._mortgage_goal.set_active()
            self.__withdraw_cash(self._mortgage_goal.mortgage.down_payment)
            return True

        return False

    def __annual_living_expenses(self) -> None:

        total_expenses = 0

        # Determines living and rent/mortgage costs
        if self._mortgage_goal is not None and self._mortgage_goal.is_active():
            if not self._mortgage_goal.mortgage.is_house_paid():
                total_expenses += self._mortgage_goal.mortgage.expected_n_cost(12)

            total_expenses += self._living_expenses.increment_year(False)

        else:
            total_expenses += self._living_expenses.increment_year(True)

        # Calculates any additional expenses
        for expense in self._expenses:
            total_expenses += expense.year_cost(self._age)

        return total_expenses

    def increment_n_years(self, n: int) -> None:
        for _ in range(n):
            # Calculate expenses

            self.__calculate_contributions()

            # Iterate to next year
            self._yearly_capital_gains_income = 0
            self._salary *= 1 + self._settings.annual_salary_increase
            self._tfsa.increment_year(
                TFSA_YEARLY_ROOM_INCREASE, self._settings.index_fund_return
            )
            # Utilizes next year salary
            self._rrsp.increment_year(self._salary, self._settings.index_fund_return)
            self._nra.increment_year(self._settings.index_fund_return)
            self._age += 1
            if (
                self._mortgage_goal.mortgage is not None
                and self._mortgage_goal.is_active()
            ):
                self._mortgage_goal.mortgage.iterate_n_months(12)

            if self._age == self._settings.retirement_age:
                self._salary = 0

    def __calculate_contributions(self) -> None:
        """Steps:
        1.  First build emergency fund
        2.  Contribute TFSA
        3.  Contribute NRA until house is purchased
        4.  Contribute TFSA and RRSP afterwards, ~15% per year total
            - Any extra cash goes towards mortgage
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
                withdrawn_cash = self.__withdraw_cash(self.__withdrawable_cash())

        bt_income = self._salary + self._yearly_capital_gains_income
        tax = tax_payable(bt_income)
        at_income = bt_income - tax

        living_expenses = self.__annual_living_expenses()
        net_positive = at_income + withdrawn_cash - living_expenses

        at_income = self._salary - tax_payable(self._salary)
        remaining_contribution_retirement = (
            self._settings.max_retirement_contribution * at_income
        )

        # If this number if negative, then we need to withdraw enough money
        if net_positive < 0:
            # Iterate until our net_positive is zero
            pass

        # Emergency Fund
        remaining_balance = self.__emergency_fund_contribution(net_positive)

        # TFSA
        remaining_contribution_retirement, remaining_balance = self.__tfsa_contribution(
            remaining_contribution_retirement, remaining_balance
        )

        # RRSP
        remaining_balance = self.__rrsp_contribution(
            remaining_contribution_retirement, remaining_balance, bt_income, at_income
        )

        #################################################################
        #                    Down Payment / NRA                         #
        #################################################################

        # Any remaining money gets contributed to the house, and anything remaining is
        # placed within in the non-registered account.
        if (
            self._mortgage_goal is not None
            and self._mortgage_goal.is_active()
            and not self._mortgage_goal.mortgage.is_house_paid()
        ):
            additional_payment = self._mortgage_goal.mortgage.additional_payment(
                remaining_balance
            )
            remaining_balance -= additional_payment

        self._nra.deposit(remaining_balance)

    def __emergency_fund_contribution(self, net_positive: float) -> float:
        # First, check the emergency fund
        required_contribution = self._emergency_fund.amount_under_limit(
            self.__annual_living_expenses() / 12
        )
        if required_contribution > 0:
            emergency_fund_deposit = min(required_contribution, net_positive)
            self._emergency_fund.deposit(emergency_fund_deposit)
            remaining_balance = net_positive - emergency_fund_deposit
        else:
            emergency_fund_withdrawal = -required_contribution
            self._emergency_fund.withdraw(emergency_fund_withdrawal)
            remaining_balance = net_positive + emergency_fund_withdrawal

        return remaining_balance

    def __tfsa_contribution(
        self, remaining_contribution_retirement: float, remaining_balance: float
    ) -> tuple:

        # Second, deposit into the TFSA account. We need to make sure we contribute the
        # required remaining retirement portion. If we currently have a mortgage, we
        # will attempt to reduce how much we contribute to the TFSA. However, if the
        # max_tfsa_asap flag is active, then we will maximize the tfsa regardless
        tfsa_retirement_amount = self._tfsa.balance * self._tfsa_retirement_portion
        if (
            self._mortgage_goal is not None
            and not self._mortgage_goal.mortgage.is_house_paid()
            and not self._settings.max_tfsa_asap
        ):
            # Either we can deposite the contribution room, the amount we need to deposit,
            # or the amount of money we have left to deposit.
            amount_deposited = min(
                self._tfsa.contribution_room,
                remaining_contribution_retirement,
                remaining_balance,
            )

            self._tfsa.deposit(amount_deposited)
            added_tfsa_retirement_portion = amount_deposited
        else:

            amount_deposited = self._tfsa.deposit(remaining_balance)

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
                self._tfsa.balance - tfsa_retirement_amount,
            ),
        )
        tfsa_retirement_amount += retirement_conversion_amount
        remaining_contribution_retirement -= retirement_conversion_amount

        # Adjust the retirement amount in the tfsa account
        if self._tfsa.balance == 0:
            self._tfsa_retirement_portion = 0
        else:
            self._tfsa_retirement_portion = tfsa_retirement_amount / self._tfsa.balance

        return remaining_contribution_retirement, remaining_balance

    def __rrsp_contribution(
        self,
        remaining_contribution_retirement: float,
        remaining_balance: float,
        bt_income: float,
        at_income: float,
    ) -> float:
        # Now, check the RRSP. If we have additional money max out the required
        # contribution for retirement. Then, pay additional to the house.
        if (
            self._mortgage_goal is not None
            and not self._mortgage_goal.mortgage.is_house_paid()
        ):
            RRSP_AT_contribution = min(
                self._rrsp.contribution_room, remaining_contribution_retirement
            )
        else:
            RRSP_AT_contribution = min(
                self._rrsp.contribution_room,
                remaining_balance,
            )

        # We need to calculate the beforetax contribution. The aftertax contribution we
        # have should be reduced by the after tax contribution

        max_BT_contribution = rrsp_before_tax_calc(
            RRSP_AT_contribution, at_income, bt_income
        )

        BT_contributed = self._rrsp.deposit(bt_income - max_BT_contribution)

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

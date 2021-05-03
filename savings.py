from saving_vessels import TFSA, RRSP, EmergencyFund, NonRegisteredAccount
from expenses import Taxes, Mortgage, LivingExpenses, DEFAULT_CHILD_COSTS

# TODO:
# - Financial Planner
# - Class for person
# - Expenses
#   - Annuity Expenses (Car)
#   - Monthly Expenses
#   - Child Expenses
# - Financial goals
#   - House
#   - Child
#   - Retirement + Retirement Age
#   - Nest Egg goal
#   - HBP ?
#   - Marriage/Car
# - Non-reg account
# - Salary increase
# - Settings to tick
#   - 15% flat each year
#   - Max RRSP/TFSA before house, or after house
#   - Max TFSA before saving for house
#
# Employer RRSP matching
# Add two person functionality
# Keep track of tax avoided by using RRSP, and add RRIF when 71
# Add retirement age
# Max allowed to contribute to mortgage

INDEX_RETURN = 0.07
TFSA_YEARLY_ROOM_INCREASE = 6000

FEDERAL_BASIC_AMOUNT = 13229
FEDERAL_BRACKETS = [FEDERAL_BASIC_AMOUNT, 48535, 97070, 150474, 214368]
FEDERAL_TAX_RATES = [0.1500, 0.2050, 0.2600, 0.2900, 0.3300]

ONTARIO_BASIC_AMOUNT = 10783
ONTARIO_BRACKETS = [ONTARIO_BASIC_AMOUNT, 44740, 89482, 150000, 220000]
ONTARIO_TAX_RATES = [0.0505, 0.0915, 0.1116, 0.1216, 0.1316]

federal_tax = Taxes(FEDERAL_BRACKETS, FEDERAL_TAX_RATES, FEDERAL_BASIC_AMOUNT)
ontario_tax = Taxes(ONTARIO_BRACKETS, ONTARIO_TAX_RATES, ONTARIO_BASIC_AMOUNT)


class Person:
    class MortgageGoal:

        _active = False

        def __init__(self, mortgage_info: Mortgage) -> None:
            self._mortgage = mortgage_info

        def is_active(self) -> bool:
            return self._active

        def set_active(self, set_to_active=True) -> None:
            self._active = set_to_active

        @property
        def mortgage(self) -> Mortgage:
            return self._mortgage

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
        max_tfsa_asap = False
        max_retirement_contribution = 0.15
        annual_salary_increase = 0.03
        retirement_age = 65

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
        self._annual_salary_increase = annual_salary_increase
        self._age = age
        self._living_expenses = living_expenses
        self._tfsa = tfsa
        self._rrsp = rrsp
        self._nra = taxable_account
        self._emergency_fund = emergency_fund

    def add_one_time_payment(self, payment_amount: float, age_paid: int) -> None:
        self._expenses.append(Expense(payment_amount, age_paid))

    def add_recurring_cost(
        self, payment_amount: float, age_first_payment: int, period_n_years: int = 1,
    ) -> None:
        self._expenses.append(Expense(payment_amount, age_paid, period_n_years))

    def new_child(self, age_have_child: float) -> None:

        if age_have_child < self._age:
            return

        self._children.append(age_have_child)

    def house_purchase(self, mortgage: Mortgage) -> None:
        # Stores the Mortgage information
        self._mortgage_goal = MortgageGoal(mortgage)

    def increment_n_years(self, n: int) -> None:
        for _ in range(n):
            # Calculate expenses
            total_expenses = 0

            if self._mortgage_goal is not None:
                # Attempt to buy the house if the house has not already been purchased
                if not self._mortgage_goal.is_active():
                    self.__purchase_house()

            taxable_income = self._salary + self._yearly_capital_gains_income

            tax_payable = self.__tax_payable(taxable_income)

            living_expenses = self.__calculate_living_expenses()
            total_losses = tax_payable + living_expenses
            net_positive = self._salary - total_losses
            __calculate_contributions(net_positive, taxable_income)

            # Iterate to next year
            self._yearly_capital_gains_income = 0
            self._salary *= 1 + self._annual_salary_increase
            self._tfsa.increment_year(TFSA_YEARLY_ROOM_INCREASE, INDEX_RETURN)
            # Utilizes next year salary
            self._rrsp.increment_year(self._salary, INDEX_RETURN)
            self._nra.increment_year(INDEX_RETURN)
            self._age += 1
            if self._age == self._settings.retirement_age:
                self._salary = 0

    def __tax_payable(self, income: float) -> float:
        return federal_tax.tax_payable(income) + ontario_tax.tax_payable(income)

    def __withdrawable_cash(self) -> float:

        withdrawable_cash = 0

        if not _settings.max_tfsa_asap:
            withdrawable_cash += self._tfsa.balance() * (
                1 - self._tfsa_retirement_portion
            )

        # This is the tax payable if the NRA account is emptied.
        additional_tax_payable = federal_tax.additional_tax_payable(
            self._salary, self._nra._balance()
        ) + ontario_tax.additional_tax_payable(self._salary, self._nra._balance())

        withdrawable_cash += self._nra._balance() - additional_tax_payable

        return withdrawable_cash

    def __withdraw_cash(self, amount: float) -> bool:

        if amount > __withdrawable_cash():
            return False

        # Manage NRA account withdrawals
        _, capital_gains = self._nra.withdraw(amount)
        self._yearly_capital_gains_income = capital_gains

        remaining_withdraw = amount - total_withdrawn

        # Manage TFSA account withdrawals
        self._tfsa_retirement_portion = (
            self._tfsa.balance * self._tfsa_retirement_portion
        ) / (self._tfsa.balance - remaining_withdraw)
        self._tfsa.withdraw(remaining_withdraw)

        return True

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

    def __calculate_living_expenses(self) -> None:

        total_expenses = 0

        # Determines living and rent/mortgage costs
        if self._mortgage_goal is not None:

            # Pay mortgage costs for the year
            if (
                self._mortgage_goal.is_active()
                and self._mortgage_goal.mortgage.is_house_paid is False
            ):
                total_expenses += self._mortgage_goal.mortgage.iterate_n_months(12)

            total_expenses += self._living_expenses.increment_year(False)

        else:
            total_expenses += self._living_expenses.increment_year(True)

        # Calculates any additional expenses
        for expense in self._expenses:
            total_expenses += expense.year_cost(self._age)

        return total_expenses

    def __rrsp_before_tax_calc(
        self, after_tax_deduction: float, before_tax_income: float
    ) -> float:
        pass

    def __calculate_contributions(self, net_positive: float, bt_income: float) -> None:
        """Steps:
            1.  First build emergency fund
            2.  Contribute TFSA
            3.  Contribute NRA until house is purchased
            4.  Contribute TFSA and RRSP afterwards, ~15% per year total
                - Any extra cash goes towards mortgage
            5.  Once mortgage is paid off, contribute additional money to
                TFSA > RRSP > NRA

        Args:
            net_positive (float): [description]
        """
        # TODO: What if this number is negative
        # TODO: Put extra cash towards mortgage
        # TODO: RRSP ?? BT money
        after_tax_income = self._salary - self.__tax_payable(self._salary)
        remaining_contribution_retirement = (
            self._settings.max_retirement_contribution * after_tax_income
        )

        # First, check the emergency fund
        required_contribution = self._emergency_fund.amount_under_limit(
            self.__calculate_living_expenses()
        )
        if required_contribution > 0:
            emergency_fund_deposit = min(required_contribution, net_positive)
            self._emergency_fund.deposit(emergency_fund_deposit)
            remaining_balance = net_positive - emergency_fund_deposit
        else:
            emergency_fund_withdrawal = -required_contribution
            self._emergency_fund.withdraw(emergency_fund_withdrawal)
            remaining_balance = net_positive + emergency_fund_withdrawal

        # Second, deposit into the TFSA account
        tfsa_retirement_amount = self._tfsa.balance * self._tfsa_retirement_portion

        if (
            _settings.max_tfsa_asap
            or self._mortgage_goal is not None
            and self._mortgage_goal.mortgage.is_house_paid()
        ):
            amount_deposited = self._tfsa.deposit(remaining_balance)

            added_tfsa_retirement_portion = min(
                amount_deposited, remaining_contribution_retirement
            )
            tfsa_retirement_amount += added_tfsa_retirement_portion
            self._tfsa_retirement_portion = tfsa_retirement_amount / self._tfsa.balance

            remaining_contribution_retirement -= added_tfsa_retirement_portion
            remaining_balance -= amount_deposited

        elif not self._mortgage_goal.mortgage.is_house_paid():
            # Either we can deposite the contribution room, the amount we need to deposit,
            # or the amount of money we have left to deposit.
            amount_deposited = min(
                self._tfsa.contribution_room,
                remaining_contribution_retirement,
                remaining_balance,
            )
            self._tfsa.deposit(amount_deposited)
            tfsa_retirement_amount += amount_deposited
            self._tfsa_retirement_portion = tfsa_retirement_amount / self._tfsa.balance

            remaining_contribution_retirement -= amount_deposited
            remaining_balance -= amount_deposited

        # Now, check the RRSP. If we have additional money max out the required
        # contribution for retirement. Then, pay additional to the house.

        # TODO: These amounts need to be before tax amount
        if (
            self._mortgage_goal is not None
            and self._mortgage_goal.mortgage.is_house_paid()
        ):
            RRSP_AT_contribution = min(self._rrsp.contribution_room, remaining_balance)
        else:
            RRSP_AT_contribution = min(
                self._rrsp.contribution_room,
                remaining_balance,
                remaining_contribution_retirement,
            )

        # The before tax contribution is the after tax contribution, plus the
        # return generated by reducing your income through the RRSP.
        BT_contribution = RRSP_AT_contribution + (
            self.__tax_payable(BT_income)
            - self.__tax_payable(BT_income - RRSP_AT_contribution)
        )
        self._rrsp.deposit(BT_contribution)

        remaining_contribution_retirement -= RRSP_AT_contribution
        remaining_balance -= RRSP_AT_contribution

        # Any remaining money gets contributed to the house, or gets placed
        # in the non-registered account.
        if self._mortgage_goal.mortgage.is_house_paid():
            pass

        else:
            pass

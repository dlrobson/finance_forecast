"""Class container holding various classes for Taxes, Mortgage, LivingExpenses, and
Expenses.
"""
from typing import List


class Taxes:
    """Class that calculates the tax required to be paid given a specific income,
    and manages the tax brackets
    """

    def __init__(self, brackets: List[float], tax_rates: List[float]) -> None:
        """Instantiates the Taxes class. Takes in corresponding brackets and taxes
        lists

        Args:
            brackets (List[float]): Tax brackets
            tax_rates (List[float]): Tax rates for the given tax brackets

        Raises:
            Exception: Return if the brackets and tax_rates are not the same length
        """
        if len(brackets) != len(tax_rates):
            raise Exception("Input array lengths do not align")

        self._brackets = brackets
        self._tax_rates = tax_rates

    def brackets(self) -> List[float]:
        """Getter for the tax brackets

        Returns:
            List[float]: Tax brackets
        """
        return self._brackets

    def tax_rates(self) -> List[float]:
        """Getter for the tax rates

        Returns:
            List[float]: Tax rates
        """
        return self._tax_rates

    def tax_payable(self, income: float) -> float:
        """Calculates the total tax to be paid for a given income. The stored tax
        brackets and rates are used for this calculation

        Args:
            income (float): Input income to calculate tax_payable

        Returns:
            float: The amount of tax that needs to be paid
        """

        # Income is less than basic amount
        if income < self.brackets()[0]:
            return 0

        total_tax_payable = 0

        for i in range(1, len(self.brackets())):

            previous_bracket_limit = self.brackets()[i - 1]
            bracket_rate = self.tax_rates()[i - 1]

            bracket_limit = self.brackets()[i]
            next_bracket_rate = self.tax_rates()[i]

            # If this is our upper tax bracket, we need to calculate the tax payable,
            # and exit the loop since we will not meet the higher brackets
            if income < bracket_limit:
                total_tax_payable += (income - previous_bracket_limit) * bracket_rate
                break

            # Now we fully met this bracket requirements, so add the maximum tax paid
            # for this bracket
            total_tax_payable += (bracket_limit - previous_bracket_limit) * bracket_rate

            # If we are within the largest tax bracket, we need to calculate the amount
            # before we exit the loop
            if i == len(self.brackets()) - 1:
                total_tax_payable += (income - bracket_limit) * next_bracket_rate

        return total_tax_payable

    def income_in_upper_bracket(self, income: float) -> float:
        """Calculates the amount of income within the upper tax bracket. Maybe helpful
        for determining an optimal RRSP contribution

        Args:
            income (float): Input income to calculate tax_payable

        Returns:
            float: Amount of income within the highest paid tax bracket
        """
        # Iterate until we find the highest bracket for the provided income, then
        # return
        for i in range(1, len(self.brackets())):

            previous_bracket_limit = self.brackets()[i - 1]
            bracket_rate = self.tax_rates()[i - 1]

            bracket_limit = self.brackets()[i]
            next_bracket_rate = self.tax_rates()[i]

            # We've found the largest bracket
            if income < bracket_limit:
                return income - previous_bracket_limit

            # The largest bracket is the last bracket
            if i == len(self.brackets()) - 1:
                return income - bracket_limit

    def additional_tax_payable(self, income: float, additional_income: float) -> float:
        """Determines the additional amount of tax that would need to be paid given an
        increase in income.

        Args:
            income (float): Base income to compare
            additional_income (float): Additional income to compare

        Returns:
            float: The extra amount of tax payable
        """
        return self.tax_payable(income + additional_income) - self.tax_payable(income)

    def increment_values(self, increment: float) -> None:
        """Increments the tax bracket values given a specific increase. Multiplies the
        bracket value by (1 + increment)

        Args:
            increment (float): Amount to multiply each bracket by
        """
        self._brackets = [x * (1 + increment) for x in self._brackets]


class Mortgage:
    def __init__(
        self,
        house_cost: float,
        down_payment: float,
        rate: float = 0.03,
        period: float = 25,
    ):
        self._rate = rate / 12
        self._period = period * 12

        # Monthly payment amount. This stays constant for the whole term, thus
        # the calculation depends on the difference between the house cost and
        # down payment amount, not the principal remaining. If you were to make
        # additional payments to pay down the principal, this would result in
        # future payments to pay more towards principal than interest.
        # https://www.bankrate.com/calculators/mortgages/mortgage-calculator.aspx
        self._monthly_payment = (
            (house_cost - down_payment)
            * (self._rate * ((1 + self._rate) ** self._period))
            / ((1 + self._rate) ** self._period - 1)
        )

        self._house_cost = house_cost
        self._down_payment = down_payment
        self._principal_remaining = house_cost - down_payment
        self._interest_paid = 0

    @property
    def down_payment(self) -> float:
        return self._down_payment

    @property
    def monthly_payment(self) -> float:
        return self._monthly_payment

    @property
    def principal_remaining(self) -> float:
        return self._principal_remaining

    @property
    def interest_paid(self) -> float:
        return self._interest_paid

    def additional_payment(self, payment: float) -> float:
        amount_paid = min(payment, self._principal_remaining)
        self._principal_remaining -= amount_paid
        return amount_paid

    def iterate_n_months(self, n: float) -> float:

        amount_paid = 0
        for _ in range(n):

            # The interest paid for the month is the accumulated interest based
            # on its monthly rate
            interest_payment = self._principal_remaining * self._rate
            # Cannot pay more than the principal itself
            principal_payment = min(
                self._monthly_payment - interest_payment, self._principal_remaining
            )

            self._interest_paid += interest_payment
            self._principal_remaining -= principal_payment
            amount_paid += interest_payment + principal_payment
            if self._principal_remaining < 0:
                break

        return amount_paid

    def expected_n_cost(self, n: float) -> float:

        amount_paid = 0
        principal = self._principal_remaining
        for _ in range(n):

            # The interest paid for the month is the accumulated interest based
            # on its monthly rate
            interest_payment = principal * self._rate
            # Cannot pay more than the principal itself
            principal_payment = min(self._monthly_payment - interest_payment, principal)

            principal -= principal_payment
            amount_paid += interest_payment + principal_payment
            if principal < 0:
                break

        return amount_paid

    def expected_payoff_months(self) -> int:

        num_months = 0
        principal_remaining = self._principal_remaining
        while True:
            num_months += 1
            # The interest paid for the month is the accumulated interest based
            # on its monthly rate
            interest_payment = principal_remaining * self._rate
            # Cannot pay more than the principal itself
            principal_payment = min(
                self._monthly_payment - interest_payment, principal_remaining
            )

            principal_remaining -= principal_payment

            if principal_remaining < 1:
                return num_months

    def is_house_paid(self) -> bool:
        return True if self._principal_remaining < 0.01 else False


DEFAULT_CHILD_COSTS = [
    1500 + 4000 / 12,
    1500,
    500,
    500,
    500,
    500,
    500,
    500,
    500,
    500,
    500,
    500,
    500,
    500,
    500,
    500,
    500,
    500,
    500,
    500,
]


class LivingExpenses:
    def __init__(
        self,
        living_costs: float,
        rent: float,
        children_ages: list = None,
        monthly_cost_per_child: list = DEFAULT_CHILD_COSTS,
    ):
        self._living_costs = living_costs
        self._rent = rent
        self._child_cost = monthly_cost_per_child
        self._children_ages = list() if children_ages is None else children_ages

    @property
    def living_costs(self):
        return self._living_costs

    @living_costs.setter
    def living_costs(self, new_living_cost: float) -> bool:
        self._living_costs = new_living_cost
        return True

    @property
    def rent(self):
        return self._rent

    @rent.setter
    def rent(self, new_rent: float) -> bool:
        self._rent = new_rent
        return True

    @property
    def child_cost(self):
        return self._child_cost

    @child_cost.setter
    def child_cost(self, new_child_cost: float) -> bool:
        self._child_cost = new_child_cost
        return True

    def add_child(self) -> None:
        self._children_ages.append(0)

    def increment_year(self, include_rent: bool = True) -> float:

        annual_expenses = 12 * self.monthly_living_costs(include_rent)

        for i in range(len(self._children_ages)):
            self._children_ages[i] += 1

        return annual_expenses

    def monthly_living_costs(self, include_rent: bool) -> float:

        total_expenses = 0

        total_expenses += self._living_costs
        if include_rent:
            total_expenses += self._rent

        for age in self._children_ages:

            if age >= len(self._child_cost):
                continue

            total_expenses += self._child_cost[age]

        return total_expenses


class Expense:
    def __init__(self, amount: float, initial_year: int, recurrance: int = 0) -> None:
        self._amount = amount
        self._initial_year = initial_year
        self._recurrance = recurrance

    def year_cost(self, year: int) -> float:
        if self._initial_year == year:
            return self._amount

        if self._recurrance == 0:
            return 0

        return (
            self._amount if (year - self._initial_year) % self._recurrance == 0 else 0
        )


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

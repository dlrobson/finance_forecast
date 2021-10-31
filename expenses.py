#!/usr/bin/env python3
"""Class container holding various classes for Taxes, Mortgage, LivingExpenses, and
Expenses.
"""
from typing import List

EI_CONTRIBUTION_PER_DOLLAR = 0.0158
EI_MAX_CONTRIBUTION = 889.54

CPP_CONTRIBUTION_PER_DOLLAR = 0.0495
CPP_MAX_CONTRIBUTION = 3166.45
CPP_CONTRIBUTION_ROOM_EXEMPT = 3500


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
            bracket_limit = self.brackets()[i]

            # We've found the largest bracket
            if income < bracket_limit:
                return income - previous_bracket_limit

        return income - self.brackets()[-1]

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
    """Mortgage class. Manages the mortgage payments for a property."""

    def __init__(
        self,
        house_cost: float,
        down_payment: float,
        rate: float = 0.03,
        period: float = 25,
    ):
        """Initializes the class with the house payment information.

        Args:
            house_cost (float): Initial full cost of the house (dollars)
            down_payment (float): Original down payment for the house (dollars)
            rate (float, optional): House interest rate. Defaults to 0.03.
            period (float, optional): House payment period. Defaults to 25.
        """
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
        """Getter for the size of the down payment

        Returns:
            float: down payment amount
        """
        return self._down_payment

    @property
    def monthly_payment(self) -> float:
        """Returns the monthly payment amount.

        Returns:
            float: Monthly payment in dollars
        """
        return self._monthly_payment

    @property
    def principal_remaining(self) -> float:
        """Remaining principal remaining for the house

        Returns:
            float: Principal remaining in dollars
        """
        return self._principal_remaining

    @property
    def interest_paid(self) -> float:
        """Interest that's been paid so far in the mortgage

        Returns:
            float: Amount of interest paid in dollars
        """
        return self._interest_paid

    def additional_payment(self, payment: float) -> float:
        """Pay an additional payment that brings down the down payment. Returns
        the amount paid as an additional payment, which caps to the current
        remaining principal.

        Args:
            payment (float): Amount to pay down the principal

        Returns:
            float: The amount paid down on the prinicpal
        """
        amount_paid = min(payment, self._principal_remaining)
        self._principal_remaining -= amount_paid
        return amount_paid

    def iterate_n_months(self, n: float) -> float:
        """Iterates the mortgage n months forward in the future. Decreases the
        remaining principal, and interest paid. Returns the amount paid during
        the iteration

        Args:
            n (float): Number of months to iterate

        Returns:
            float: The amount paid for the duration
        """

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
        """Copy of iterate_n_months function, however this does not affect the
        internal variables. Good for predictions. A description of
        iterate_n_months:

        Iterates the mortgage n months forward in the future. Decreases the
        remaining principal, and interest paid. Returns the amount paid during
        the iteration

        Args:
            n (float): Number of months to iterate

        Returns:
            float: The amount paid for the duration
        """

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
        """The expected number of months required to fully pay off the mortgage

        Returns:
            int: The number of months required to pay off the mortgage.
        """
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
        """Asserts whether the house has been fully paid. It is assumed paid
        if less than 0.01 dollars remain in the principal.

        Returns:
            bool: True if no principal remains in the mortgage.
        """
        return self._principal_remaining < 0.01


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
    """Simple class to keep track of the living expenses. It is capable of
    determining the monthly costs given the number of children, rent/mortgage,
    and expected monthly expenses.
    """

    def __init__(
        self,
        living_costs: float,
        rent: float,
        children_ages: list = None,
        monthly_cost_per_child: list = None,
    ):
        """Initializer for the Living expenses class.

        Args:
            living_costs (float): Expected living expenses in dollars.

            rent (float): Expected monthly rental cost

            children_ages (list, optional): A list containing the current ages
            of the children. The child ages will be maintained. Defaults to
            None.

            monthly_cost_per_child (list, optional): Monthly costs per child
            given their age. Each entry in the list is the monthly cost of the
            child for the corresponding index. Defaults to None.
        """
        self._living_costs = living_costs
        self._rent = rent
        self._children_ages = list() if children_ages is None else children_ages
        self._child_cost = (
            DEFAULT_CHILD_COSTS
            if monthly_cost_per_child is None
            else monthly_cost_per_child
        )

    @property
    def living_costs(self) -> float:
        """Living costs getter.

        Returns:
            float: Living costs in dollars
        """
        return self._living_costs

    @living_costs.setter
    def living_costs(self, new_living_cost: float) -> bool:
        """Living costs setter

        Args:
            new_living_cost (float): New monthly living cost

        Returns:
            bool: Returns True if successfully replaced the living costs
        """
        self._living_costs = new_living_cost
        return True

    @property
    def rent(self) -> float:
        """Rent getter

        Returns:
            float: Monthly rent costs in dollars
        """
        return self._rent

    @rent.setter
    def rent(self, new_rent: float) -> bool:
        """Monthly rent

        Args:
            new_rent (float): New monthly rent

        Returns:
            bool: Returns true if successfully replaced old rent variable
        """
        self._rent = new_rent
        return True

    @property
    def child_cost(self) -> List[int]:
        """Returns the monthly child cost list.

        Returns:
            List[int]: List containing the monthly child costs
        """
        return self._child_cost

    def add_child(self) -> None:
        """Add a new child to the current child list. Adds a new child at age 0"""
        self._children_ages.append(0)

    def increment_year(self, include_rent: bool = True) -> float:
        """Increment the living expenses fully a year. Increments the ages of
        each child, and returns the yearly living costs.

        Args:
            include_rent (bool, optional): Indicates whether to include rental
            costs in the calculation. False maybe applicable if you are
            currently paying a mortgage. Defaults to True.

        Returns:
            float: Total amount paid for the year
        """

        annual_expenses = 12 * self.monthly_living_costs(include_rent)

        for i in range(len(self._children_ages)):
            self._children_ages[i] += 1

        return annual_expenses

    def monthly_living_costs(self, include_rent: bool) -> float:
        """Calculates the monthly living costs, and returns it.

        Args:
            include_rent (bool): Flag about whether to include rental costs in
            the final value.

        Returns:
            float: Monthly costs
        """
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
    """General purpose expense class to keep track of miscellaneous expenses."""

    def __init__(self, amount: float, initial_year: int, recurrance: int = 0) -> None:
        """Expense initializer. Either an expense is attached to a single year, or
        is a recurring expense, which occurs at a yearly interval.

        Args:
            amount (float): Amount paid at the expense payment time
            initial_year (int): Initial payment year of the expense, or the only year
            if it is a non-recurring expense
            recurrance (int, optional): Number of years in between payments for a
            recurring expense. Defaults to 0, which indicates that it is a single-time
            expense (non-recurring).
        """
        self._amount = amount
        self._initial_year = initial_year
        self._recurrance = recurrance

    def year_cost(self, year: int) -> float:
        """Calculates the year costs for this expense. Based on the payment nature of
        the expense, determines whether there a payment for the input year.

        Args:
            year (int): Year to verify whether a payment is required for this expense

        Returns:
            float: The amount required to be paid for the input year.
        """
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

FEDERAL_TAX = Taxes(FEDERAL_BRACKETS, FEDERAL_TAX_RATES)
ONTARIO_TAX = Taxes(ONTARIO_BRACKETS, ONTARIO_TAX_RATES)


def tax_payable(income: float) -> float:
    """Calculates the Ontario and Federal tax required for the input income.

    Args:
        income (float): Income to determine tax payable.

    Returns:
        float: Required Federal and Ontario tax to pay.
    """
    return FEDERAL_TAX.tax_payable(income) + ONTARIO_TAX.tax_payable(income)


def ei_contribution(income: float) -> float:
    return min(EI_MAX_CONTRIBUTION, EI_CONTRIBUTION_PER_DOLLAR * income)


def cpp_contribution(income: float) -> float:
    return min(
        CPP_MAX_CONTRIBUTION,
        (income - CPP_CONTRIBUTION_ROOM_EXEMPT) * CPP_CONTRIBUTION_PER_DOLLAR,
    )

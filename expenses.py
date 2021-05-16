class Taxes:
    def __init__(self, brackets: list, tax_rates: list):
        if len(brackets) != len(tax_rates):
            raise Exception("Input array lengths do not align")

        self._brackets = brackets
        self._tax_rates = tax_rates

    def brackets(self):
        return self._brackets

    def tax_rates(self):
        return self._tax_rates

    def tax_payable(self, income: float) -> float:

        if income < self.brackets()[0]:
            return 0

        total_tax_payable = 0

        for i in range(1, len(self.brackets())):

            previous_bracket_limit = self.brackets()[i - 1]
            bracket_rate = self.tax_rates()[i - 1]

            bracket_limit = self.brackets()[i]
            next_bracket_rate = self.tax_rates()[i]

            if income < bracket_limit:
                total_tax_payable += (income - previous_bracket_limit) * bracket_rate
                break

            # Now we fully met this bracket requirements.
            total_tax_payable += (bracket_limit - previous_bracket_limit) * bracket_rate

            if i == len(self.brackets()) - 1:
                total_tax_payable += (income - bracket_limit) * next_bracket_rate

        return total_tax_payable

    def tax_paid_upper_bracket(self, income: float) -> float:
        for i in range(1, len(self.brackets())):

            previous_bracket_limit = self.brackets()[i - 1]
            bracket_rate = self.tax_rates()[i - 1]

            bracket_limit = self.brackets()[i]
            next_bracket_rate = self.tax_rates()[i]

            if income < bracket_limit:
                return (income - previous_bracket_limit) * bracket_rate

            if i == len(self.brackets()) - 1:
                return (income - bracket_limit) * next_bracket_rate

    def additional_tax_payable(self, income: float, additional_income: float) -> float:
        return self.tax_payable(income + additional_income) - self.tax_payable(income)

    def increment_values(self, increment: float) -> None:
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
        children_ages: list = [],
        monthly_cost_per_child: list = DEFAULT_CHILD_COSTS,
    ):
        self._living_costs = living_costs
        self._rent = rent
        self._child_cost = monthly_cost_per_child
        self._children_ages = children_ages

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
    def __init__(self, amount: float, initial_age: int, recurrance: int = 0) -> None:
        self._amount = amount
        self._initial_age = initial_age
        self._recurrance = recurrance

    def year_cost(self, age: int) -> float:
        if self._initial_age == age:
            return amount

        if self._recurrance == 0:
            return 0

        return self._amount if (age - self._initial_age) % self._recurrance == 0 else 0

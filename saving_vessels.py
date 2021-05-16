from abc import ABC, abstractmethod

RRSP_ROOM_PERCENT = 0.18


class RegisteredAccount(ABC):
    @property
    def balance(self):
        return self._balance

    @property
    def contribution_room(self):
        return self._contribution_room

    def deposit(self, amount: float) -> float:
        if amount < 0:
            return 0

        deposit_amount = min(self._contribution_room, amount)
        self._balance += deposit_amount
        self._contribution_room -= deposit_amount
        return deposit_amount

    @abstractmethod
    def withdraw(self, amount: float) -> float:
        pass

    @abstractmethod
    def increment_year(self, *args, **kwargs) -> None:
        pass


class TFSA(RegisteredAccount):
    class Settings:
        tfsa_yearly_room_increase = 6000

    @property
    def settings(self) -> Settings:
        return self._settings

    @settings.setter
    def settings(self, new_settings: Settings) -> None:
        self._settings = new_settings

    _settings = Settings()

    def __init__(self, balance: float, contribution_room: float):
        self._balance = max(balance, 0)
        self._contribution_room = max(contribution_room, 0)
        self._curr_year_withdrawals = 0

    def withdraw(self, amount: float) -> float:
        if amount < 0:
            return 0

        withdraw_amount = min(self._balance, amount)
        self._curr_year_withdrawals += withdraw_amount
        self._balance -= withdraw_amount
        return withdraw_amount

    def increment_year(self, interest_rate: float) -> None:
        self._balance *= 1 + interest_rate
        self._contribution_room += (
            self._settings.tfsa_yearly_room_increase + self._curr_year_withdrawals
        )
        self._curr_year_withdrawals = 0


class RRSP(RegisteredAccount):
    def __init__(
        self,
        balance: float,
        contribution_room: float,
        max_room: float = 27230,
        max_room_percent_income: float = 0.18,
    ):
        self._balance = max(balance, 0)
        self._contribution_room = max(contribution_room, 0)
        self._max_room = max_room
        self._max_room_percent_income = 0.18

    def withdraw(self, amount: float) -> float:
        if amount < 0:
            return 0

        withdraw_amount = min(self._balance, amount)
        self._balance -= withdraw_amount
        return withdraw_amount

    def increment_year(
        self, income: float, interest_rate: float, room_increment: float = 0.0
    ) -> float:
        self._balance *= 1 + interest_rate
        room_increase = min(self._max_room, income * self._max_room_percent_income)
        self._max_room *= 1 + room_increment
        self._contribution_room += room_increase

        return room_increase


class EmergencyFund:
    def __init__(self, balance: float, emergency_months: float = 6):
        self._balance = max(balance, 0)
        self._emergency_months = emergency_months

    @property
    def balance(self):
        return self._balance

    @property
    def emergency_months(self):
        return self._emergency_months

    @emergency_months.setter
    def emergency_months(self, new_emergency_months: float) -> float:
        self._emergency_months = max(0, new_emergency_months)

    def withdraw(self, amount: float) -> float:
        if amount < 0:
            return 0

        withdraw_amount = min(self._balance, amount)
        self._balance -= withdraw_amount
        return withdraw_amount

    def amount_under_limit(self, monthly_expenses: float) -> float:
        return self._emergency_months * monthly_expenses - self._balance

    def deposit(self, amount: float) -> float:
        if amount < 0:
            return 0

        self._balance += amount


class NonRegisteredAccount:
    def __init__(self, balance: float, investment_costs: float) -> None:
        self._balance = balance
        self._investment_costs = investment_costs

    @property
    def balance(self) -> float:
        return self._balance

    def deposit(self, amount: float) -> None:
        self._balance += amount
        self._investment_costs += amount

    def withdraw(self, amount: float) -> tuple:
        """Withdraw from the account. Returns the taxable capital gains income.
        https://www.wealthsimple.com/en-ca/learn/capital-gains-tax-canada#sample_calculation_of_tax_on_a_capital_gain
        Args:
            amount (float): amount to withdraw

        Returns:
            float: taxable capital gains
        """

        if self._balance == 0:
            return (0, 0)

        # Can only withdraw up to the balance of the account
        amount = min(amount, self._balance)

        capital_gains = (self._balance - self._investment_costs) * (
            amount / self._balance
        )

        self._investment_costs *= 1 - (amount / self._balance)

        self._balance -= amount
        # 0.5, since half of capital gains are taxable
        return (amount, 0.5 * capital_gains)

    def capital_gains(self, amount: float) -> float:
        if self._balance == 0:
            return 0

        # Can only withdraw up to the balance of the account
        amount = min(amount, self._balance)

        capital_gains = (self._balance - self._investment_costs) * (
            amount / self._balance
        )

        # 0.5, since half of capital gains are taxable
        return 0.5 * capital_gains

    def increment_year(self, growth: float) -> None:
        self._balance *= 1 + growth

#!/usr/bin/env python3
from expenses import tax_payable
from saving_vessels import RRSP, TFSA, EmergencyFund, NonRegisteredAccount

INDEX_RETURN = 0.07


class Person:
    def __init__(
        self,
        age: int,
        yearly_salary_BT: float,
        tfsa: TFSA,
        rrsp: RRSP,
        taxable_account: NonRegisteredAccount,
        emergency_fund: EmergencyFund,
    ) -> None:
        self._salary = yearly_salary_BT
        self._age = age
        self._tfsa = tfsa
        self._rrsp = rrsp
        self._nra = taxable_account
        self._emergency_fund = emergency_fund

    def withdrawable_cash(
        self, after_tax_calc: bool = True, include_retirement: bool = False
    ) -> float:
        """After tax maximum withdrawable amount

        Returns:
            float: The maximum amount after tax that is withdrawn
        """
        withdrawable_cash = 0
        additional_taxable_income = 0
        # RRSP
        if include_retirement:
            withdrawable_cash += self._rrsp.balance
            additional_taxable_income += self._rrsp.balance

            withdrawable_cash += self._tfsa.balance

        elif not self._settings.allow_tfsa_withdrawal:
            withdrawable_cash += self._tfsa.balance * (
                1 - self._tfsa_retirement_portion
            )

        # NRA
        withdrawable_cash += self._nra._balance
        additional_taxable_income += self._nra.capital_gains(self._nra.balance)

        if not after_tax_calc:
            return withdrawable_cash

        # This is the tax payable if the NRA account is emptied.
        additional_tax_payable = tax_payable(
            self._salary
            + additional_taxable_income
            + self._yearly_investment_taxable_income
        ) - tax_payable(self._salary + self._yearly_investment_taxable_income)

        withdrawable_cash -= additional_tax_payable

        return withdrawable_cash

    def withdraw_cash(self, amount: float) -> float:

        # withdraw 0 if the requested amount is greater than the maximum allowed
        if amount > self.withdrawable_cash(False, include_retirement=True):
            return 0

        # Manage NRA account withdrawals
        total_withdrawn, capital_gains = self._nra.withdraw(amount)
        self._yearly_investment_taxable_income += capital_gains

        remaining_withdraw = amount - total_withdrawn

        if remaining_withdraw > 0 and self._tfsa_retirement_portion < 1.0:
            # Manage TFSA account withdrawals
            self._tfsa_retirement_portion = (
                self._tfsa.balance * self._tfsa_retirement_portion
            ) / (self._tfsa.balance - remaining_withdraw)

            total_withdrawn += self._tfsa.withdraw(remaining_withdraw)

            remaining_withdraw = amount - total_withdrawn

        # If more needs to be withdrawn, dive into retirements.
        if remaining_withdraw > 0:
            rrsp_withdrawal = self._rrsp.withdraw(
                min(self._rrsp.balance, remaining_withdraw)
            )
            total_withdrawn += rrsp_withdrawal
            self._yearly_investment_taxable_income += rrsp_withdrawal

        remaining_withdraw = amount - total_withdrawn

        if remaining_withdraw > 0:
            total_withdrawn += self._tfsa.withdraw(remaining_withdraw)

        return total_withdrawn

    class Settings:
        allow_tfsa_withdrawal = True
        max_retirement_contribution = 0.15
        annual_salary_increase = 0.03
        retirement_age = 65
        index_fund_return = INDEX_RETURN

    _settings = Settings()
    _tfsa_retirement_portion = 0
    _yearly_investment_taxable_income = 0

    @property
    def settings(self) -> Settings:
        return self._settings

    @settings.setter
    def settings(self, new_settings: Settings) -> None:
        self._settings = new_settings

    @property
    def age(self) -> int:
        return self._age

    @property
    def tfsa(self) -> TFSA:
        return self._tfsa

    @property
    def rrsp(self) -> RRSP:
        return self._rrsp

    @property
    def nra(self) -> NonRegisteredAccount:
        return self._nra

    @property
    def tfsa_retirement_portion(self) -> float:
        return self._tfsa_retirement_portion

    @tfsa_retirement_portion.setter
    def tfsa_retirement_portion(self, new_tfsa_retirement_portion: float) -> None:
        self._tfsa_retirement_portion = new_tfsa_retirement_portion

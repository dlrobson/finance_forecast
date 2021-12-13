#!/usr/bin/env python3
from copy import deepcopy

from expenses import LivingExpenses, Mortgage
from financial_unit import FinancialUnit, Person
from saving_vessels import RRSP, TFSA, EmergencyFund, NonRegisteredAccount
from utils import plot_balances


# TODO:
# - Financial goals
#   - Nest Egg goal. Retire immediately after?
#   - HBP ?
# - Settings to tick
#   - Max RRSP/TFSA before house, or after house
#
# Ontario surtax: https://paycheckguru.com/tax-brackets-and-marginal-tax-rates-in-canada/ontario-personal-marginal-income-tax-rates-2/
# House expenses should be included, property tax etc
# Employer RRSP matching
# Keep track of tax avoided by using RRSP, and add RRIF when 71
# Max allowed to contribute to mortgage
# Multiple houses/properties/rental properties
# Comments everywhere
# Cap salary
# RESP - no
# RRIF would be very insightful
# CPP 15% tax credit based on contribution
# If retired, withdraw amount to deposit into TFSA
# Graph with bar with divisions. Mortgage Interest, mortgage principal, EF, TFSA, RRSP, NRA contributions, expenses

if __name__ == "__main__":

    age = 26
    tfsa = TFSA(53000, 0)
    rrsp = RRSP(0, 40000)
    nra = NonRegisteredAccount(40000, 0)
    emergency_fund = EmergencyFund(6000)
    salary = 70000
    person = Person(age, salary, tfsa, rrsp, nra, emergency_fund)
    settings = person.settings
    settings.allow_tfsa_withdrawal = True
    settings.retirement_age = 65
    settings.max_retirement_contribution = 1.0
    settings.annual_salary_increase = 0.02
    person.settings = settings
    people = [person]

    # person2 = deepcopy(person)
    # person2._salary = 65000
    # people = [person, person2]

    expenses = LivingExpenses(1000, 1250)
    finances = FinancialUnit(2022, people, expenses)

    financial_unit_settings = finances.settings
    financial_unit_settings.pay_house_down_asap = True
    finances.settings = financial_unit_settings
    people = [person]

    mortgage = Mortgage(800000, 160000)
    finances.house_purchase(mortgage)
    finances.increment_n_years(65 - 26)
    plot_balances(finances._balance_tracker, rrsp_scale=0.70, nra_scale=0.80)

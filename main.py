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

    age = 23
    tfsa = TFSA(15000, 20000)
    rrsp = RRSP(0, 18000)
    nra = NonRegisteredAccount(0, 0)
    emergency_fund = EmergencyFund(6000)
    salary = 100000
    person = Person(age, salary, tfsa, rrsp, nra, emergency_fund)
    settings = person.settings
    settings.allow_tfsa_withdrawal = True
    settings.retirement_age = 50
    settings.max_retirement_contribution = 0.29
    settings.annual_salary_increase = 0.02
    person.settings = settings

    person2 = deepcopy(person)
    person2._salary = 100000

    people = [person, person2]
    # people = [person]

    expenses = LivingExpenses(1500, 2000)
    finances = FinancialUnit(2022, people, expenses)

    mortgage = Mortgage(800000, 160000)
    finances.house_purchase(mortgage)
    finances.increment_n_years(27)
    print(settings.max_retirement_contribution)
    plot_balances(finances._balance_tracker, rrsp_scale=0.70, nra_scale=0.80)

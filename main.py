from copy import deepcopy

from expenses import LivingExpenses, Mortgage
from financial_unit import FinancialUnit, Person
from saving_vessels import RRSP, TFSA, EmergencyFund, NonRegisteredAccount

if __name__ == "__main__":

    age = 25
    tfsa = TFSA(52000, 0)
    rrsp = RRSP(0, 28426)
    nra = NonRegisteredAccount(0, 0)
    emergency_fund = EmergencyFund(3000)
    salary = 65000

    person = Person(age, salary, tfsa, rrsp, nra, emergency_fund)
    settings = person.settings
    settings.allow_tfsa_withdrawal = True
    person.settings = settings

    person2 = deepcopy(person)

    people = [person, person2]

    expenses = LivingExpenses(600, 1250)
    finances = FinancialUnit(2020, people, expenses)

    # age = 23
    # expenses = LivingExpenses(400, 1200)
    # tfsa = TFSA(10000, 30000)
    # rrsp = RRSP(0, 15000)
    # nra = NonRegisteredAccount(0, 0)
    # emergency_fund = EmergencyFund(5000)
    # salary = 65000
    # person = Person(age, expenses, salary, tfsa, rrsp, nra, emergency_fund)

    mortgage = Mortgage(800000, 160000)
    finances.house_purchase(mortgage)

    for _ in range(43):
        for person_i in range(len(finances.persons)):
            print(
                "Age: {:.2f}\t Salary: {:.2f}\t EF: {:.2f}\t TFSA: {:.2f}\t RRSP: {:.2f}"
                "\t NRA: {:.2f}\t Mortgage Remaining: {:.2f}".format(
                    finances.persons[person_i].age,
                    finances.persons[person_i]._salary,
                    finances.persons[person_i]._emergency_fund.balance,
                    finances.persons[person_i]._tfsa.balance,
                    finances.persons[person_i]._rrsp.balance,
                    finances.persons[person_i]._nra.balance,
                    finances._mortgage_goal.mortgage.principal_remaining,
                )
            )
        finances.increment_n_years(1)

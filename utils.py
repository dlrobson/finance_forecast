#!/usr/bin/env python3
from financial_unit import BalanceTracker
import matplotlib.pyplot as plt
import numpy as np


def plot_balances(
    data: BalanceTracker, rrsp_scale: float = 1.0, nra_scale: float = 1.0
) -> None:
    fig, ax = plt.subplots()
    years = data._years
    tfsa_data = np.array(data._tfsa_balance)
    rrsp_data = np.array(data._rrsp_balance) * rrsp_scale
    nra_data = np.array(data._nra_balance) * nra_scale
    house_principal = np.array(data._mortgage_principal)
    emergency_fund = np.array(data._emergency_fund)

    ax.bar(years, emergency_fund, label="Emergency Fund")
    ax.bar(years, tfsa_data, bottom=emergency_fund, label="TFSA")
    ax.bar(years, rrsp_data, bottom=tfsa_data + emergency_fund, label="RRSP")
    ax.bar(
        years,
        nra_data,
        bottom=rrsp_data + tfsa_data + emergency_fund,
        label="NRA",
    )
    ax.bar(
        years,
        house_principal,
        bottom=rrsp_data + tfsa_data + nra_data + emergency_fund,
        label="House Principal",
    )

    ax.set_xlabel("Year")
    ax.set_ylabel("Adjusted Balance ($)")
    ax.set_title("Net Worth")
    ax.legend()
    print(
        tfsa_data[-1]
        + rrsp_data[-1]
        + nra_data[-1]
        + house_principal[-1]
        + emergency_fund[-1]
    )
    plt.show()

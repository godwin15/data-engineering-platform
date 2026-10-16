
import pandas as pd
from faker import Faker
from datetime import date, timedelta
from pathlib import Path
import random

fake = Faker()
Faker.seed(42)
random.seed(42)

ORGANIZATIONS = ["ORG001", "ORG002", "ORG003"]

START_DATE = date(2026, 10, 1)
PROCESSING_DATES = [
    START_DATE + timedelta(days=i)
    for i in range(7)
]

OUTPUT_DIR = Path("data/raw")


def generate_clients():
    records = []

    for org_id in ORGANIZATIONS:
        # Create each client once, then repeat their
        # stable identity across daily snapshots.
        clients = []

        for client_number in range(1, 11):
            clients.append({
                "organisation_id": org_id,
                "client_id": f"C{client_number:04d}",
                "client_name": fake.name(),
                "email": fake.email(),
                "country": "USA",
                "risk_profile": random.choice([
                    "Conservative", "Moderate", "Aggressive"
                ]),
                "account_status": random.choice([
                    "Active", "Inactive"
                ])
            })

        for processing_date in PROCESSING_DATES:
            for client in clients:
                records.append({
                    **client,
                    "processing_date": str(processing_date)
                })

    return pd.DataFrame(records)


def generate_accounts(clients_df):
    records = []

    # Each client gets two accounts.
    unique_clients = clients_df[
        ["organisation_id", "client_id"]
    ].drop_duplicates()

    for _, client in unique_clients.iterrows():
        for account_number in range(1, 3):
            account_id = (
                f"{client['client_id']}-A{account_number}"
            )

            account_type = random.choice([
                "Brokerage", "Retirement", "Savings"
            ])

            opening_balance = round(
                random.uniform(1000, 100000), 2
            )

            for processing_date in PROCESSING_DATES:
                records.append({
                    "organisation_id": client["organisation_id"],
                    "processing_date": str(processing_date),
                    "account_id": account_id,
                    "client_id": client["client_id"],
                    "account_type": account_type,
                    "currency": "USD",
                    "opening_balance": opening_balance
                })

    return pd.DataFrame(records)


def generate_portfolios(accounts_df):
    records = []

    # Give each account a stable investment strategy
    unique_accounts = accounts_df[
        ["organisation_id", "account_id"]
    ].drop_duplicates()

    for _, account in unique_accounts.iterrows():
        strategy = random.choice([
            "Growth", "Income", "Balanced"
        ])

        account_snapshots = accounts_df[
            (accounts_df["organisation_id"] == account["organisation_id"]) &
            (accounts_df["account_id"] == account["account_id"])
        ]

        for _, snapshot in account_snapshots.iterrows():
            records.append({
                "organisation_id": snapshot["organisation_id"],
                "processing_date": snapshot["processing_date"],
                "portfolio_id": f"P-{snapshot['account_id']}",
                "account_id": snapshot["account_id"],
                "portfolio_name": "Managed Investment Portfolio",
                "investment_strategy": strategy,
                "base_currency": "USD"
            })

    return pd.DataFrame(records)


def generate_securities():
    records = []

    securities = [
        ("SEC001", "Apple Inc.", "AAPL", "Stock"),
        ("SEC002", "Microsoft Corp.", "MSFT", "Stock"),
        ("SEC003", "Vanguard S&P 500 ETF", "VOO", "ETF"),
        ("SEC004", "US Treasury Bond", "UST", "Bond"),
        ("SEC005", "NVIDIA Corp.", "NVDA", "Stock")
    ]

    for org_id in ORGANIZATIONS:
        for processing_date in PROCESSING_DATES:
            for security_id, name, ticker, asset_type in securities:
                records.append({
                    "organisation_id": org_id,
                    "processing_date": str(processing_date),
                    "security_id": security_id,
                    "security_name": name,
                    "ticker": ticker,
                    "asset_type": asset_type,
                    "currency": "USD"
                })

    return pd.DataFrame(records)


def generate_holdings(portfolios_df, securities_df):
    records = []

    for _, portfolio in portfolios_df.iterrows():
        org_id = portfolio["organisation_id"]
        processing_date = portfolio["processing_date"]

        available_securities = securities_df[
            (securities_df["organisation_id"] == org_id) &
            (securities_df["processing_date"] == processing_date)
        ]

        # Three securities per portfolio
        selected = available_securities.head(3)

        for _, security in selected.iterrows():
            quantity = random.randint(5, 100)
            unit_price = round(random.uniform(50, 500), 2)

            records.append({
                "organisation_id": org_id,
                "processing_date": processing_date,
                "holding_id": (
                    f"{portfolio['portfolio_id']}-"
                    f"{security['security_id']}"
                ),
                "portfolio_id": portfolio["portfolio_id"],
                "security_id": security["security_id"],
                "quantity": quantity,
                "unit_price": unit_price,
                "market_value": round(quantity * unit_price, 2)
            })

    return pd.DataFrame(records)


def generate_transactions(accounts_df):
    records = []

    for _, account in accounts_df.iterrows():
        amount = round(random.uniform(100, 5000), 2)
        transaction_type = random.choice([
            "Deposit", "Withdrawal", "Dividend"
        ])

        records.append({
            "organisation_id": account["organisation_id"],
            "processing_date": account["processing_date"],
            "transaction_id": f"T-{account['account_id']}-"
                              f"{account['processing_date']}",
            "account_id": account["account_id"],
            "transaction_type": transaction_type,
            "amount": amount,
            "currency": "USD"
        })

    return pd.DataFrame(records)


def generate_trades(accounts_df, securities_df):
    records = []

    for _, account in accounts_df.iterrows():
        org_id = account["organisation_id"]
        processing_date = account["processing_date"]

        available = securities_df[
            (securities_df["organisation_id"] == org_id) &
            (securities_df["processing_date"] == processing_date)
        ]

        security = available.iloc[0]

        quantity = random.randint(1, 20)
        price = round(random.uniform(50, 500), 2)

        records.append({
            "organisation_id": org_id,
            "processing_date": processing_date,
            "trade_id": f"TR-{account['account_id']}-"
                        f"{processing_date}",
            "account_id": account["account_id"],
            "security_id": security["security_id"],
            "trade_type": random.choice(["Buy", "Sell"]),
            "quantity": quantity,
            "price": price,
            "trade_value": round(quantity * price, 2)
        })

    return pd.DataFrame(records)


def generate_advisors(clients_df):
    records = []

    for org_id in ORGANIZATIONS:
        # Three advisors per organization
        advisors = []

        for advisor_number in range(1, 4):
            advisors.append({
                "organisation_id": org_id,
                "advisor_id": f"ADV{advisor_number:03d}",
                "advisor_name": fake.name(),
                "specialization": random.choice([
                    "Retirement Planning",
                    "Investment Management",
                    "Wealth Advisory"
                ]),
                "status": "Active"
            })

        for processing_date in PROCESSING_DATES:
            for advisor in advisors:
                records.append({
                    **advisor,
                    "processing_date": str(processing_date)
                })

    return pd.DataFrame(records)



def generate_fees(accounts_df):
    records = []

    for _, account in accounts_df.iterrows():
        fee_amount = round(
            account["opening_balance"] * 0.0001, 2
        )

        records.append({
            "organisation_id": account["organisation_id"],
            "processing_date": account["processing_date"],
            "fee_id": (
                f"F-{account['account_id']}-"
                f"{account['processing_date']}"
            ),
            "account_id": account["account_id"],
            "fee_type": "Management Fee",
            "fee_amount": fee_amount,
            "currency": "USD"
        })

    return pd.DataFrame(records)


def generate_statements(accounts_df, transactions_df, fees_df):
    records = []

    for _, account in accounts_df.iterrows():
        org_id = account["organisation_id"]
        processing_date = account["processing_date"]
        account_id = account["account_id"]

        txns = transactions_df[
            (transactions_df["organisation_id"] == org_id) &
            (transactions_df["processing_date"] == processing_date) &
            (transactions_df["account_id"] == account_id)
        ]

        fees = fees_df[
            (fees_df["organisation_id"] == org_id) &
            (fees_df["processing_date"] == processing_date) &
            (fees_df["account_id"] == account_id)
        ]

        deposits = txns.loc[
            txns["transaction_type"].isin(["Deposit", "Dividend"]),
            "amount"
        ].sum()

        withdrawals = txns.loc[
            txns["transaction_type"] == "Withdrawal",
            "amount"
        ].sum()

        total_fees = fees["fee_amount"].sum()

        ending_balance = round(
            account["opening_balance"]
            + deposits
            - withdrawals
            - total_fees,
            2
        )

        records.append({
            "organisation_id": org_id,
            "processing_date": processing_date,
            "statement_id": f"S-{account_id}-{processing_date}",
            "account_id": account_id,
            "opening_balance": account["opening_balance"],
            "total_deposits": round(deposits, 2),
            "total_withdrawals": round(withdrawals, 2),
            "total_fees": round(total_fees, 2),
            "ending_balance": ending_balance,
            "currency": "USD"
        })

    return pd.DataFrame(records)


def save_dataset(df, table_name):
    folder = OUTPUT_DIR / table_name
    folder.mkdir(parents=True, exist_ok=True)

    path = folder / f"{table_name}.csv"
    df.to_csv(path, index=False)

    print(f"{table_name}: {len(df)} records saved")



if __name__ == "__main__":
    clients_df = generate_clients()
    accounts_df = generate_accounts(clients_df)
    portfolios_df = generate_portfolios(accounts_df)
    securities_df = generate_securities()

    holdings_df = generate_holdings(
        portfolios_df, securities_df
    )
    transactions_df = generate_transactions(accounts_df)
    trades_df = generate_trades(
        accounts_df, securities_df
    )
    advisors_df = generate_advisors(clients_df)
    fees_df = generate_fees(accounts_df)
    statements_df = generate_statements(
        accounts_df, transactions_df, fees_df
    )

    datasets = {
        "clients": clients_df,
        "accounts": accounts_df,
        "portfolios": portfolios_df,
        "securities": securities_df,
        "holdings": holdings_df,
        "transactions": transactions_df,
        "trades": trades_df,
        "advisors": advisors_df,
        "fees": fees_df,
        "statements": statements_df
    }

    for name, df in datasets.items():
        save_dataset(df, name)

    print("\nValidation:")

    keys = {
        "clients": "client_id",
        "accounts": "account_id",
        "portfolios": "portfolio_id",
        "securities": "security_id",
        "holdings": "holding_id",
        "transactions": "transaction_id",
        "trades": "trade_id",
        "advisors": "advisor_id",
        "fees": "fee_id",
        "statements": "statement_id"
    }

    # Check duplicate business keys within each snapshot
    for name, df in datasets.items():
        assert not df.duplicated([
            "organisation_id", "processing_date", keys[name]
        ]).any(), f"Duplicate records found in {name}"

    # Check child-parent relationships within the same
    # organization and processing date
    relationships = [
        (accounts_df, clients_df, ["client_id"]),
        (portfolios_df, accounts_df, ["account_id"]),
        (holdings_df, portfolios_df, ["portfolio_id"]),
        (holdings_df, securities_df, ["security_id"]),
        (transactions_df, accounts_df, ["account_id"]),
        (trades_df, accounts_df, ["account_id"]),
        (trades_df, securities_df, ["security_id"]),
        (fees_df, accounts_df, ["account_id"]),
        (statements_df, accounts_df, ["account_id"])
    ]

    for child, parent, foreign_keys in relationships:
        join_columns = [
            "organisation_id",
            "processing_date"
        ] + foreign_keys

        check = child.merge(
            parent[join_columns].drop_duplicates(),
            on=join_columns,
            how="left",
            indicator=True,
            validate="many_to_one"
        )

        assert (check["_merge"] == "both").all(), (
            f"Invalid relationship for {foreign_keys}"
        )

    # Validate statement balance calculations
    calculated_balance = (
        statements_df["opening_balance"]
        + statements_df["total_deposits"]
        - statements_df["total_withdrawals"]
        - statements_df["total_fees"]
    ).round(2)

    assert (
        calculated_balance == statements_df["ending_balance"]
    ).all(), "Statement balance mismatch"

    print("All validation checks passed!")


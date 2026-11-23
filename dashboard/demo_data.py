"""
Money Mate Analytics: Demo Data Service
Loads and serves synthetic data for Demo Mode.
"""
import os
import pandas as pd
from datetime import datetime

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data')

DEMO_USERS = {
    1: {"name": "Aarav Sharma", "role": "Tech Professional", "salary": "₹30,000/mo"},
    2: {"name": "Riya Patel", "role": "UX Designer", "salary": "₹35,000/mo"},
    3: {"name": "Kabir Verma", "role": "Product Lead", "salary": "₹40,000/mo"}
}

def load_demo_bundle():
    """Load all CSVs into DataFrames."""
    tx = pd.read_csv(os.path.join(DATA_DIR, 'transactions.csv'))
    users = pd.read_csv(os.path.join(DATA_DIR, 'users.csv'))
    cats = pd.read_csv(os.path.join(DATA_DIR, 'categories.csv'))
    wallets = pd.read_csv(os.path.join(DATA_DIR, 'wallets.csv'))
    budgets = pd.read_csv(os.path.join(DATA_DIR, 'budgets.csv'))
    goals = pd.read_csv(os.path.join(DATA_DIR, 'goals.csv'))

    tx['transaction_date'] = pd.to_datetime(tx['transaction_date'])
    tx['month'] = tx['transaction_date'].dt.to_period('M').astype(str)
    tx['weekday'] = tx['transaction_date'].dt.day_name()

    budgets['start_date'] = pd.to_datetime(budgets['start_date'])
    budgets['end_date'] = pd.to_datetime(budgets['end_date'])
    budgets['month'] = budgets['start_date'].dt.to_period('M').astype(str)

    return tx, users, cats, wallets, budgets, goals


def get_demo_monthly_summary(user_id, selected_months=None):
    tx, _, _, _, _, _ = load_demo_bundle()
    filtered = tx[tx.user_id == user_id]
    if selected_months:
        filtered = filtered[filtered.month.isin(selected_months)]

    monthly = filtered.groupby(['month', 'type'])['amount'].sum().unstack(fill_value=0).reset_index()
    if 'income' not in monthly.columns:
        monthly['income'] = 0.0
    if 'expense' not in monthly.columns:
        monthly['expense'] = 0.0
    return monthly.sort_values('month')


def get_demo_category_spend(user_id, selected_months=None):
    tx, _, _, _, _, _ = load_demo_bundle()
    filtered = tx[(tx.user_id == user_id) & (tx.type == 'expense')]
    if selected_months:
        filtered = filtered[filtered.month.isin(selected_months)]
    res = filtered.groupby('category_name')['amount'].sum().reset_index()
    res.columns = ['category', 'spend']
    return res.sort_values('spend', ascending=False)


def get_demo_wallet_usage(user_id, selected_months=None):
    tx, _, _, _, _, _ = load_demo_bundle()
    filtered = tx[(tx.user_id == user_id) & (tx.type == 'expense')]
    if selected_months:
        filtered = filtered[filtered.month.isin(selected_months)]
    res = filtered.groupby('wallet_name').agg(
        txn_count=('amount', 'count'),
        spend=('amount', 'sum')
    ).reset_index()
    res.rename(columns={'wallet_name': 'wallet'}, inplace=True)
    return res.sort_values('spend', ascending=False)


def get_demo_budget_status(user_id, selected_months=None):
    tx, _, cats, _, budgets, _ = load_demo_bundle()
    bu = budgets[budgets.user_id == user_id]
    if selected_months:
        bu = bu[bu.month.isin(selected_months)]

    cat_map = cats[cats.user_id == user_id].set_index('category_id')['name'].to_dict()
    rows = []
    for _, b in bu.iterrows():
        cat_name = cat_map.get(b['category_id'], 'Other')
        actual = tx[
            (tx.user_id == user_id) &
            (tx.category_id == b['category_id']) &
            (tx.type == 'expense') &
            (tx.transaction_date >= b['start_date']) &
            (tx.transaction_date <= b['end_date'])
        ]['amount'].sum()
        pct = round((actual / b['amount'] * 100), 1) if b['amount'] > 0 else 0
        rows.append({
            'budget_id': _ + 1,
            'month': b['month'],
            'category': cat_name,
            'budget': b['amount'],
            'spent': actual,
            'used_pct': pct
        })
    return pd.DataFrame(rows)


def get_demo_anomalies(user_id):
    tx, _, _, _, _, _ = load_demo_bundle()
    exp = tx[(tx.user_id == user_id) & (tx.type == 'expense')].copy()
    avg_cat = exp.groupby('category_name')['amount'].mean().to_dict()
    exp['avg_amt'] = exp['category_name'].map(avg_cat).round(1)
    exp['ratio'] = (exp['amount'] / exp['avg_amt']).round(1)
    anomalies = exp[exp['ratio'] > 3].sort_values('amount', ascending=False)
    anomalies.rename(columns={'category_name': 'category', 'wallet_name': 'wallet'}, inplace=True)
    return anomalies[['transaction_date', 'category', 'title', 'amount', 'ratio', 'avg_amt', 'wallet']]


def get_demo_goals(user_id):
    _, _, _, _, _, goals = load_demo_bundle()
    return goals[goals.user_id == user_id].copy()


def get_demo_transactions(user_id, limit=None, selected_months=None):
    tx, _, _, _, _, _ = load_demo_bundle()
    filtered = tx[tx.user_id == user_id].copy()
    if selected_months:
        filtered = filtered[filtered.month.isin(selected_months)]
    filtered.sort_values('transaction_date', ascending=False, inplace=True)
    if limit:
        filtered = filtered.head(limit)
    return filtered

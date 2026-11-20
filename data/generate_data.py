"""
Money Mate Analytics: Data Generator
Generates 12 months of realistic synthetic finance data for 3 users.
Writes to MySQL AND exports CSVs for Streamlit Cloud deployment.
"""
import random
import os
import pandas as pd
from datetime import date, timedelta
from sqlalchemy import create_engine
from dotenv import load_dotenv

load_dotenv()
random.seed(42)

# --- Config ---
MYSQL_USER = os.getenv('MYSQL_USER', 'root')
MYSQL_PASS = os.getenv('MYSQL_PASSWORD', 'password')
MYSQL_HOST = os.getenv('MYSQL_HOST', 'localhost')
MYSQL_PORT = os.getenv('MYSQL_PORT', '3306')
MYSQL_DB   = os.getenv('MYSQL_DB', 'money_mate')

USE_MYSQL = True
try:
    engine = create_engine(
        f'mysql+pymysql://{MYSQL_USER}:{MYSQL_PASS}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DB}'
    )
    with engine.connect() as conn:
        conn.execute(conn.connection.cursor().execute("SELECT 1") or conn)
    print("✅ Connected to MySQL")
except Exception as e:
    print(f"⚠️  MySQL connection failed: {e}")
    print("   Will generate CSV files only.")
    USE_MYSQL = False
    engine = None

# --- Data Generation ---
START, END = date(2025, 12, 1), date(2026, 11, 30)
names = ['Aarav', 'Riya', 'Kabir']

users = pd.DataFrame({
    'user_id': [1, 2, 3],
    'name': names,
    'email': [n.lower() + '@example.com' for n in names],
    'password_hash': ['demo'] * 3
})

expense_cats = ['Food', 'Rent', 'Transport', 'Shopping', 'Entertainment', 'Bills', 'Health', 'Education']
income_cats = ['Salary', 'Freelance']
wallet_types = {'Cash': 'cash', 'Bank': 'bank', 'UPI': 'upi', 'Credit Card': 'card'}

cats, wallets, cat_id, wal_id = [], [], {}, {}
cid = wid = 1
for u in users.user_id:
    for c in expense_cats + income_cats:
        t = 'expense' if c in expense_cats else 'income'
        cats.append({'category_id': cid, 'user_id': u, 'name': c, 'type': t})
        cat_id[(u, c)] = cid
        cid += 1
    for w, t in wallet_types.items():
        wallets.append({
            'wallet_id': wid, 'user_id': u, 'name': w, 'type': t,
            'initial_balance': 10000, 'current_balance': 10000
        })
        wal_id[(u, w)] = wid
        wid += 1

# Transaction generation
daily = {
    'Food': (0.8, 80, 450), 'Transport': (0.5, 30, 300),
    'Shopping': (0.12, 300, 3000), 'Entertainment': (0.1, 150, 1200),
    'Health': (0.03, 200, 2500)
}
w_names = ['UPI', 'Cash', 'Credit Card', 'Bank']
w_probs = [0.55, 0.15, 0.20, 0.10]

rows = []
def add(u, cat, amt, typ, d, w):
    rows.append({
        'user_id': u, 'category_id': cat_id[(u, cat)],
        'wallet_id': wal_id[(u, w)], 'amount': amt,
        'type': typ, 'title': cat, 'transaction_date': d
    })

d = START
while d <= END:
    for u in users.user_id:
        if d.day == 1:
            add(u, 'Salary', 25000 + u * 5000, 'income', d, 'Bank')
        if d.day == 5:
            add(u, 'Rent', 8000, 'expense', d, 'Bank')
        if d.day == 10:
            add(u, 'Bills', 1200 + random.randint(0, 600), 'expense', d, 'Bank')
        if d.day == 15:
            add(u, 'Education', 1500, 'expense', d, 'UPI')
        if d.day == 20 and random.random() < 0.4:
            add(u, 'Freelance', random.randint(3000, 9000), 'income', d, 'Bank')
        for cat, (p, lo, hi) in daily.items():
            if cat == 'Shopping' and d.month in (10, 11):
                p = p * 2  # festival season spike
            if random.random() < p:
                w = random.choices(w_names, weights=w_probs)[0]
                add(u, cat, round(random.uniform(lo, hi)), 'expense', d, w)
    d += timedelta(days=1)

tx = pd.DataFrame(rows)

# Inject anomalies
idx = tx[(tx.type == 'expense') & (tx.title != 'Rent')].index
for i in random.sample(list(idx), 8):
    tx.loc[i, 'amount'] = tx.loc[i, 'amount'] * 8

# Budgets
budget_amt = {
    'Food': 6000, 'Rent': 8000, 'Transport': 2500, 'Shopping': 4000,
    'Entertainment': 1500, 'Bills': 2000, 'Health': 1000, 'Education': 2000
}
budgets = []
for u in users.user_id:
    for s in pd.date_range(START, periods=12, freq='MS'):
        e = (s + pd.offsets.MonthEnd(0)).date()
        for c, a in budget_amt.items():
            budgets.append({
                'user_id': u, 'category_id': cat_id[(u, c)],
                'amount': a, 'period': 'monthly',
                'start_date': s.date(), 'end_date': e
            })

# Goals
goals = []
for u in users.user_id:
    goals.append({
        'user_id': u, 'name': 'New Laptop', 'target_amount': 60000,
        'current_amount': 15000 * u, 'target_date': date(2027, 3, 31), 'status': 'active'
    })
    goals.append({
        'user_id': u, 'name': 'Goa Trip', 'target_amount': 25000,
        'current_amount': 5000 * u, 'target_date': date(2027, 1, 31), 'status': 'active'
    })

# --- Write to MySQL ---
if USE_MYSQL and engine:
    try:
        users.to_sql('users', engine, if_exists='append', index=False)
        pd.DataFrame(cats).to_sql('categories', engine, if_exists='append', index=False)
        pd.DataFrame(wallets).to_sql('wallets', engine, if_exists='append', index=False)
        tx.to_sql('transactions', engine, if_exists='append', index=False)
        pd.DataFrame(budgets).to_sql('budgets', engine, if_exists='append', index=False)
        pd.DataFrame(goals).to_sql('goals', engine, if_exists='append', index=False)
        print(f'✅ MySQL: {len(tx)} transactions inserted')
    except Exception as e:
        print(f'⚠️  MySQL write failed: {e}')

# --- Export CSVs (for Streamlit Cloud deployment) ---
DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')
os.makedirs(DATA_DIR, exist_ok=True)

# Add category names and wallet names to transactions for CSV
cats_df = pd.DataFrame(cats)
wallets_df = pd.DataFrame(wallets)

tx_full = tx.merge(
    cats_df[['category_id', 'name', 'type']].rename(columns={'name': 'category_name', 'type': 'category_type'}),
    on='category_id', how='left'
)
tx_full = tx_full.merge(
    wallets_df[['wallet_id', 'name']].rename(columns={'name': 'wallet_name'}),
    on='wallet_id', how='left'
)

users.to_csv(os.path.join(DATA_DIR, 'users.csv'), index=False)
cats_df.to_csv(os.path.join(DATA_DIR, 'categories.csv'), index=False)
wallets_df.to_csv(os.path.join(DATA_DIR, 'wallets.csv'), index=False)
tx_full.to_csv(os.path.join(DATA_DIR, 'transactions.csv'), index=False)
pd.DataFrame(budgets).to_csv(os.path.join(DATA_DIR, 'budgets.csv'), index=False)
pd.DataFrame(goals).to_csv(os.path.join(DATA_DIR, 'goals.csv'), index=False)

print(f'✅ CSVs exported to {DATA_DIR}/')
print(f'   Total transactions: {len(tx)}')
print(f'   Date range: {START} to {END}')
print(f'   Users: {", ".join(names)}')

"""
Money Mate Analytics: SQLite Database Layer
Handles all database operations — works locally and on Streamlit Cloud.
"""
import sqlite3
import os
import bcrypt
import pandas as pd
from datetime import date, datetime

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data', 'money_mate.db')


def get_conn():
    """Get a SQLite connection with foreign keys enabled."""
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Create all tables if they don't exist."""
    conn = get_conn()
    cur = conn.cursor()

    cur.executescript("""
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        phone TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS categories (
        category_id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        name TEXT NOT NULL,
        type TEXT NOT NULL CHECK(type IN ('income','expense')),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(user_id)
    );

    CREATE TABLE IF NOT EXISTS wallets (
        wallet_id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        name TEXT NOT NULL,
        type TEXT NOT NULL CHECK(type IN ('cash','bank','upi','card')),
        initial_balance REAL DEFAULT 0,
        current_balance REAL DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(user_id)
    );

    CREATE TABLE IF NOT EXISTS transactions (
        transaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        category_id INTEGER NOT NULL,
        wallet_id INTEGER NOT NULL,
        amount REAL NOT NULL CHECK(amount > 0),
        type TEXT NOT NULL CHECK(type IN ('income','expense')),
        title TEXT,
        description TEXT,
        transaction_date DATE NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(user_id),
        FOREIGN KEY (category_id) REFERENCES categories(category_id),
        FOREIGN KEY (wallet_id) REFERENCES wallets(wallet_id)
    );

    CREATE TABLE IF NOT EXISTS budgets (
        budget_id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        category_id INTEGER NOT NULL,
        amount REAL NOT NULL,
        period TEXT DEFAULT 'monthly' CHECK(period IN ('weekly','monthly')),
        start_date DATE NOT NULL,
        end_date DATE NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(user_id),
        FOREIGN KEY (category_id) REFERENCES categories(category_id)
    );

    CREATE TABLE IF NOT EXISTS goals (
        goal_id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        name TEXT NOT NULL,
        target_amount REAL NOT NULL,
        current_amount REAL DEFAULT 0,
        target_date DATE,
        description TEXT,
        status TEXT DEFAULT 'active' CHECK(status IN ('active','completed')),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(user_id)
    );

    CREATE TABLE IF NOT EXISTS reminders (
        reminder_id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        title TEXT NOT NULL,
        description TEXT,
        reminder_date DATE NOT NULL,
        is_recurring TEXT DEFAULT 'N',
        recurrence_type TEXT CHECK(recurrence_type IN ('daily','weekly','monthly')),
        status TEXT DEFAULT 'active' CHECK(status IN ('active','completed')),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(user_id)
    );

    CREATE INDEX IF NOT EXISTS idx_txn_user_date ON transactions(user_id, transaction_date);
    CREATE INDEX IF NOT EXISTS idx_txn_category ON transactions(category_id);
    """)

    conn.commit()
    conn.close()


# ============================================================
# AUTH FUNCTIONS
# ============================================================

def register_user(name, email, password, phone=''):
    """Register a new user. Returns (success: bool, message: str)."""
    conn = get_conn()
    try:
        pw_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        conn.execute(
            "INSERT INTO users (name, email, password_hash, phone) VALUES (?, ?, ?, ?)",
            (name, email, pw_hash, phone)
        )
        conn.commit()
        user_id = conn.execute("SELECT user_id FROM users WHERE email = ?", (email,)).fetchone()[0]

        # Create default categories for the new user
        default_expense = ['Food', 'Rent', 'Transport', 'Shopping', 'Entertainment', 'Bills', 'Health', 'Education']
        default_income = ['Salary', 'Freelance', 'Investment', 'Other Income']
        for cat in default_expense:
            conn.execute("INSERT INTO categories (user_id, name, type) VALUES (?, ?, 'expense')", (user_id, cat))
        for cat in default_income:
            conn.execute("INSERT INTO categories (user_id, name, type) VALUES (?, ?, 'income')", (user_id, cat))

        # Create default wallets
        default_wallets = [('Cash', 'cash'), ('Bank Account', 'bank'), ('UPI', 'upi'), ('Credit Card', 'card')]
        for name_w, type_w in default_wallets:
            conn.execute(
                "INSERT INTO wallets (user_id, name, type, initial_balance, current_balance) VALUES (?, ?, ?, 0, 0)",
                (user_id, name_w, type_w)
            )

        conn.commit()
        conn.close()
        return True, "Account created successfully! 🎉"
    except sqlite3.IntegrityError:
        conn.close()
        return False, "Email already registered. Try logging in."
    except Exception as e:
        conn.close()
        return False, f"Error: {str(e)}"


def login_user(email, password):
    """Login a user. Returns (success: bool, user_dict or error_msg)."""
    conn = get_conn()
    row = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
    conn.close()

    if row is None:
        return False, "No account found with this email."

    if bcrypt.checkpw(password.encode('utf-8'), row['password_hash'].encode('utf-8')):
        return True, {
            'user_id': row['user_id'],
            'name': row['name'],
            'email': row['email'],
            'phone': row['phone']
        }
    else:
        return False, "Incorrect password."


# ============================================================
# CATEGORY FUNCTIONS
# ============================================================

def get_categories(user_id, cat_type=None):
    conn = get_conn()
    if cat_type:
        rows = conn.execute(
            "SELECT * FROM categories WHERE user_id = ? AND type = ? ORDER BY name",
            (user_id, cat_type)
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM categories WHERE user_id = ? ORDER BY type, name",
            (user_id,)
        ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def add_category(user_id, name, cat_type):
    conn = get_conn()
    try:
        conn.execute(
            "INSERT INTO categories (user_id, name, type) VALUES (?, ?, ?)",
            (user_id, name, cat_type)
        )
        conn.commit()
        conn.close()
        return True, "Category added!"
    except Exception as e:
        conn.close()
        return False, str(e)


def delete_category(category_id):
    conn = get_conn()
    try:
        conn.execute("DELETE FROM categories WHERE category_id = ?", (category_id,))
        conn.commit()
        conn.close()
        return True, "Category deleted."
    except Exception as e:
        conn.close()
        return False, f"Cannot delete: {e}"


# ============================================================
# WALLET FUNCTIONS
# ============================================================

def get_wallets(user_id):
    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM wallets WHERE user_id = ? ORDER BY name", (user_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def add_wallet(user_id, name, wallet_type, initial_balance=0):
    conn = get_conn()
    try:
        conn.execute(
            "INSERT INTO wallets (user_id, name, type, initial_balance, current_balance) VALUES (?, ?, ?, ?, ?)",
            (user_id, name, wallet_type, initial_balance, initial_balance)
        )
        conn.commit()
        conn.close()
        return True, "Wallet added!"
    except Exception as e:
        conn.close()
        return False, str(e)


def delete_wallet(wallet_id):
    conn = get_conn()
    try:
        conn.execute("DELETE FROM wallets WHERE wallet_id = ?", (wallet_id,))
        conn.commit()
        conn.close()
        return True, "Wallet deleted."
    except Exception as e:
        conn.close()
        return False, f"Cannot delete: {e}"


# ============================================================
# TRANSACTION FUNCTIONS
# ============================================================

def add_transaction(user_id, category_id, wallet_id, amount, txn_type, title, description, txn_date):
    conn = get_conn()
    try:
        conn.execute(
            """INSERT INTO transactions
               (user_id, category_id, wallet_id, amount, type, title, description, transaction_date)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (user_id, category_id, wallet_id, amount, txn_type, title, description, str(txn_date))
        )
        # Update wallet balance
        if txn_type == 'income':
            conn.execute("UPDATE wallets SET current_balance = current_balance + ? WHERE wallet_id = ?",
                         (amount, wallet_id))
        else:
            conn.execute("UPDATE wallets SET current_balance = current_balance - ? WHERE wallet_id = ?",
                         (amount, wallet_id))
        conn.commit()
        conn.close()
        return True, "Transaction added! ✅"
    except Exception as e:
        conn.close()
        return False, str(e)


def get_transactions(user_id, limit=None):
    conn = get_conn()
    query = """
        SELECT t.*, c.name AS category_name, w.name AS wallet_name
        FROM transactions t
        JOIN categories c ON c.category_id = t.category_id
        JOIN wallets w ON w.wallet_id = t.wallet_id
        WHERE t.user_id = ?
        ORDER BY t.transaction_date DESC, t.transaction_id DESC
    """
    if limit:
        query += f" LIMIT {limit}"
    rows = conn.execute(query, (user_id,)).fetchall()
    conn.close()
    return pd.DataFrame([dict(r) for r in rows]) if rows else pd.DataFrame()


def delete_transaction(transaction_id, user_id):
    conn = get_conn()
    try:
        # Get transaction details to reverse wallet balance
        txn = conn.execute(
            "SELECT wallet_id, amount, type FROM transactions WHERE transaction_id = ? AND user_id = ?",
            (transaction_id, user_id)
        ).fetchone()
        if txn:
            if txn['type'] == 'income':
                conn.execute("UPDATE wallets SET current_balance = current_balance - ? WHERE wallet_id = ?",
                             (txn['amount'], txn['wallet_id']))
            else:
                conn.execute("UPDATE wallets SET current_balance = current_balance + ? WHERE wallet_id = ?",
                             (txn['amount'], txn['wallet_id']))
            conn.execute("DELETE FROM transactions WHERE transaction_id = ?", (transaction_id,))
            conn.commit()
        conn.close()
        return True, "Transaction deleted."
    except Exception as e:
        conn.close()
        return False, str(e)


# ============================================================
# BUDGET FUNCTIONS
# ============================================================

def get_budgets(user_id):
    conn = get_conn()
    rows = conn.execute(
        """SELECT b.*, c.name AS category_name
           FROM budgets b JOIN categories c ON c.category_id = b.category_id
           WHERE b.user_id = ? ORDER BY b.start_date DESC""",
        (user_id,)
    ).fetchall()
    conn.close()
    return pd.DataFrame([dict(r) for r in rows]) if rows else pd.DataFrame()


def add_budget(user_id, category_id, amount, period, start_date, end_date):
    conn = get_conn()
    try:
        conn.execute(
            """INSERT INTO budgets (user_id, category_id, amount, period, start_date, end_date)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (user_id, category_id, amount, period, str(start_date), str(end_date))
        )
        conn.commit()
        conn.close()
        return True, "Budget set! ✅"
    except Exception as e:
        conn.close()
        return False, str(e)


def delete_budget(budget_id):
    conn = get_conn()
    conn.execute("DELETE FROM budgets WHERE budget_id = ?", (budget_id,))
    conn.commit()
    conn.close()


# ============================================================
# GOAL FUNCTIONS
# ============================================================

def get_goals(user_id):
    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM goals WHERE user_id = ? ORDER BY status, target_date",
        (user_id,)
    ).fetchall()
    conn.close()
    return pd.DataFrame([dict(r) for r in rows]) if rows else pd.DataFrame()


def add_goal(user_id, name, target_amount, current_amount, target_date, description=''):
    conn = get_conn()
    try:
        conn.execute(
            """INSERT INTO goals (user_id, name, target_amount, current_amount, target_date, description)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (user_id, name, target_amount, current_amount, str(target_date), description)
        )
        conn.commit()
        conn.close()
        return True, "Goal created! 🎯"
    except Exception as e:
        conn.close()
        return False, str(e)


def update_goal_amount(goal_id, new_amount):
    conn = get_conn()
    conn.execute("UPDATE goals SET current_amount = ? WHERE goal_id = ?", (new_amount, goal_id))
    # Mark as completed if target reached
    conn.execute(
        "UPDATE goals SET status = 'completed' WHERE goal_id = ? AND current_amount >= target_amount",
        (goal_id,)
    )
    conn.commit()
    conn.close()


def delete_goal(goal_id):
    conn = get_conn()
    conn.execute("DELETE FROM goals WHERE goal_id = ?", (goal_id,))
    conn.commit()
    conn.close()


# ============================================================
# ANALYTICS FUNCTIONS
# ============================================================

def get_monthly_summary(user_id):
    conn = get_conn()
    rows = conn.execute("""
        SELECT strftime('%%Y-%%m', transaction_date) AS month,
               SUM(CASE WHEN type = 'income' THEN amount ELSE 0 END) AS income,
               SUM(CASE WHEN type = 'expense' THEN amount ELSE 0 END) AS expense
        FROM transactions WHERE user_id = ?
        GROUP BY month ORDER BY month
    """, (user_id,)).fetchall()
    conn.close()
    return pd.DataFrame([dict(r) for r in rows]) if rows else pd.DataFrame()


def get_category_spend(user_id, start_date=None, end_date=None):
    conn = get_conn()
    query = """
        SELECT c.name AS category, SUM(t.amount) AS spend
        FROM transactions t JOIN categories c ON c.category_id = t.category_id
        WHERE t.user_id = ? AND t.type = 'expense'
    """
    params = [user_id]
    if start_date:
        query += " AND t.transaction_date >= ?"
        params.append(str(start_date))
    if end_date:
        query += " AND t.transaction_date <= ?"
        params.append(str(end_date))
    query += " GROUP BY c.name ORDER BY spend DESC"
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return pd.DataFrame([dict(r) for r in rows]) if rows else pd.DataFrame()


def get_wallet_usage(user_id):
    conn = get_conn()
    rows = conn.execute("""
        SELECT w.name AS wallet, COUNT(*) AS txn_count, SUM(t.amount) AS spend
        FROM transactions t JOIN wallets w ON w.wallet_id = t.wallet_id
        WHERE t.user_id = ? AND t.type = 'expense'
        GROUP BY w.name ORDER BY spend DESC
    """, (user_id,)).fetchall()
    conn.close()
    return pd.DataFrame([dict(r) for r in rows]) if rows else pd.DataFrame()


def get_budget_status(user_id):
    """Get budget vs actual for all active budgets."""
    conn = get_conn()
    rows = conn.execute("""
        SELECT b.budget_id, b.amount AS budget,
               strftime('%%Y-%%m', b.start_date) AS month,
               c.name AS category,
               COALESCE(
                 (SELECT SUM(t.amount) FROM transactions t
                  WHERE t.category_id = b.category_id AND t.user_id = b.user_id
                  AND t.type = 'expense'
                  AND t.transaction_date >= b.start_date AND t.transaction_date <= b.end_date),
               0) AS spent
        FROM budgets b
        JOIN categories c ON c.category_id = b.category_id
        WHERE b.user_id = ?
        ORDER BY b.start_date DESC, c.name
    """, (user_id,)).fetchall()
    conn.close()
    df = pd.DataFrame([dict(r) for r in rows]) if rows else pd.DataFrame()
    if len(df) > 0:
        df['used_pct'] = (df['spent'] / df['budget'] * 100).round(1)
    return df


def get_anomalies(user_id):
    conn = get_conn()
    rows = conn.execute("""
        SELECT t.transaction_id, t.transaction_date, c.name AS category,
               t.amount, t.title, w.name AS wallet,
               a.avg_amt
        FROM transactions t
        JOIN categories c ON c.category_id = t.category_id
        JOIN wallets w ON w.wallet_id = t.wallet_id
        JOIN (
            SELECT category_id, AVG(amount) AS avg_amt
            FROM transactions WHERE type = 'expense' AND user_id = ?
            GROUP BY category_id
        ) a ON a.category_id = t.category_id
        WHERE t.type = 'expense' AND t.user_id = ? AND t.amount > 3 * a.avg_amt
        ORDER BY t.amount DESC
    """, (user_id, user_id)).fetchall()
    conn.close()
    return pd.DataFrame([dict(r) for r in rows]) if rows else pd.DataFrame()


# Initialize DB on import
init_db()

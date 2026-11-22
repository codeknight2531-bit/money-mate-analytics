"""
Money Mate: Personal Finance Analytics Dashboard
Dynamic multi-user app with authentication and CRUD operations.
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from sklearn.linear_model import LinearRegression
import numpy as np
from datetime import date, timedelta
import os
import sys

# Add dashboard dir to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import database as db

# --- Page Config ---
st.set_page_config(
    page_title='💰 Money Mate',
    page_icon='💰',
    layout='wide',
    initial_sidebar_state='expanded'
)

# --- Custom CSS ---
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0;
    }
    .sub-header { font-size: 1.1rem; color: #888; margin-top: -10px; }
    .success-box {
        padding: 12px 20px; border-radius: 10px;
        background: linear-gradient(135deg, #2ecc7122, #27ae6022);
        border-left: 4px solid #2ecc71; margin: 10px 0;
    }
    .warning-box {
        padding: 12px 20px; border-radius: 10px;
        background: linear-gradient(135deg, #e74c3c22, #c0392b22);
        border-left: 4px solid #e74c3c; margin: 10px 0;
    }
</style>
""", unsafe_allow_html=True)

# --- Session State Init ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'user' not in st.session_state:
    st.session_state.user = None


# ============================================================
# AUTH PAGE
# ============================================================
def show_auth_page():
    """Show login/signup page."""
    col_spacer1, col_main, col_spacer2 = st.columns([1, 2, 1])

    with col_main:
        st.markdown('<p class="main-header">💰 Money Mate</p>', unsafe_allow_html=True)
        st.markdown('<p class="sub-header">Your Personal Finance Analytics Dashboard</p>', unsafe_allow_html=True)
        st.markdown("---")

        tab_login, tab_signup = st.tabs(["🔐 Login", "📝 Sign Up"])

        with tab_login:
            with st.form("login_form"):
                st.subheader("Welcome Back!")
                email = st.text_input("📧 Email", placeholder="you@example.com")
                password = st.text_input("🔑 Password", type="password", placeholder="Enter password")
                submit = st.form_submit_button("Login", use_container_width=True, type="primary")

                if submit:
                    if not email or not password:
                        st.error("Please fill in all fields.")
                    else:
                        success, result = db.login_user(email, password)
                        if success:
                            st.session_state.logged_in = True
                            st.session_state.user = result
                            st.rerun()
                        else:
                            st.error(result)

        with tab_signup:
            with st.form("signup_form"):
                st.subheader("Create Account")
                name = st.text_input("👤 Full Name", placeholder="Aarav Sharma")
                email = st.text_input("📧 Email", placeholder="you@example.com", key="signup_email")
                phone = st.text_input("📱 Phone (optional)", placeholder="+91 98765 43210")
                password = st.text_input("🔑 Password", type="password", placeholder="Min 6 characters", key="signup_pass")
                password2 = st.text_input("🔑 Confirm Password", type="password", placeholder="Re-enter password")
                submit = st.form_submit_button("Create Account", use_container_width=True, type="primary")

                if submit:
                    if not name or not email or not password:
                        st.error("Please fill in all required fields.")
                    elif len(password) < 6:
                        st.error("Password must be at least 6 characters.")
                    elif password != password2:
                        st.error("Passwords don't match.")
                    else:
                        success, msg = db.register_user(name, email, password, phone)
                        if success:
                            st.success(msg + " You can now login.")
                        else:
                            st.error(msg)

        st.markdown("---")
        st.markdown(
            '<div style="text-align:center; color:#666; font-size:0.85rem;">'
            '🔒 Your data is private. Each user sees only their own finances.</div>',
            unsafe_allow_html=True
        )


# ============================================================
# SIDEBAR
# ============================================================
def show_sidebar():
    """Show sidebar with user info and navigation."""
    user = st.session_state.user
    st.sidebar.markdown(f"### 👋 Hello, {user['name']}!")
    st.sidebar.caption(f"📧 {user['email']}")
    st.sidebar.markdown("---")

    page = st.sidebar.radio(
        "📂 Navigation",
        ["📊 Dashboard", "➕ Add Transaction", "💳 Manage Wallets",
         "📁 Categories", "📋 Budget Manager", "🎯 Goals", "📜 All Transactions"],
        label_visibility="collapsed"
    )

    st.sidebar.markdown("---")
    if st.sidebar.button("🚪 Logout", use_container_width=True):
        st.session_state.logged_in = False
        st.session_state.user = None
        st.rerun()

    return page


# ============================================================
# DASHBOARD PAGE
# ============================================================
def show_dashboard():
    user_id = st.session_state.user['user_id']

    st.markdown('<p class="main-header">📊 Dashboard</p>', unsafe_allow_html=True)
    st.markdown("---")

    # Quick stats
    monthly = db.get_monthly_summary(user_id)

    if len(monthly) == 0:
        st.info("🚀 **Welcome!** Start by adding your first transaction from the sidebar.")
        st.markdown("""
        **Quick Start:**
        1. 📁 Check **Categories** — default ones are ready
        2. 💳 Set up your **Wallets** with initial balances
        3. ➕ **Add Transactions** — income & expenses
        4. 📋 Set **Budgets** for spending categories
        5. 🎯 Create **Goals** to track savings
        """)
        return

    income_total = monthly['income'].sum()
    expense_total = monthly['expense'].sum()
    savings = income_total - expense_total
    savings_rate = (savings / income_total * 100) if income_total > 0 else 0

    txns = db.get_transactions(user_id)
    num_txns = len(txns)

    # KPI Cards
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("💵 Total Income", f"₹{income_total:,.0f}")
    c2.metric("💸 Total Expense", f"₹{expense_total:,.0f}")
    c3.metric("🏦 Net Savings", f"₹{savings:,.0f}", delta=f"{savings_rate:.1f}% rate")
    c4.metric("📝 Transactions", f"{num_txns:,}")

    st.markdown("---")

    # Charts Row 1
    col1, col2 = st.columns([3, 2])

    with col1:
        st.subheader("📈 Monthly Income vs Expense")
        fig = go.Figure()
        fig.add_trace(go.Bar(x=monthly['month'], y=monthly['income'],
                             name='Income', marker_color='#2ecc71'))
        fig.add_trace(go.Bar(x=monthly['month'], y=monthly['expense'],
                             name='Expense', marker_color='#e74c3c'))
        fig.update_layout(barmode='group', height=400,
                          xaxis_title='Month', yaxis_title='Amount (₹)',
                          legend=dict(orientation="h", yanchor="bottom", y=1.02))
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("🍩 Spending by Category")
        cat_spend = db.get_category_spend(user_id)
        if len(cat_spend) > 0:
            fig2 = px.pie(cat_spend, values='spend', names='category',
                          color_discrete_sequence=px.colors.qualitative.Set3, hole=0.4)
            fig2.update_traces(textposition='inside', textinfo='percent+label')
            fig2.update_layout(height=400, showlegend=False)
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.info("No expense data yet.")

    # Charts Row 2
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("💳 Payment Method Split")
        wallet_data = db.get_wallet_usage(user_id)
        if len(wallet_data) > 0:
            fig = px.bar(wallet_data, x='wallet', y='spend', color='wallet',
                         text='txn_count', color_discrete_sequence=px.colors.qualitative.Pastel,
                         labels={'spend': 'Total Spend (₹)', 'wallet': 'Method'})
            fig.update_traces(texttemplate='%{text} txns', textposition='outside')
            fig.update_layout(height=350, showlegend=False)
            st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("📅 Savings Rate Trend")
        if len(monthly) > 1:
            monthly['savings_rate'] = ((monthly['income'] - monthly['expense']) / monthly['income'] * 100).round(1)
            monthly['savings_rate'] = monthly['savings_rate'].fillna(0)
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=monthly['month'], y=monthly['savings_rate'],
                mode='lines+markers+text',
                text=monthly['savings_rate'].astype(str) + '%',
                textposition='top center', line=dict(color='#3498db', width=3),
                marker=dict(size=10)
            ))
            fig.add_hline(y=20, line_dash="dash", line_color="green",
                          annotation_text="20% Target")
            fig.update_layout(height=350, yaxis_title='Savings Rate (%)')
            st.plotly_chart(fig, use_container_width=True)

    # Budget Status Quick View
    st.subheader("📋 Budget Status")
    budget_df = db.get_budget_status(user_id)
    if len(budget_df) > 0:
        over = budget_df[budget_df['used_pct'] > 100]
        if len(over) > 0:
            st.warning(f"⚠️ **{len(over)}** budget(s) exceeded!")
        cols = st.columns(min(len(budget_df.groupby('category')), 4))
        latest = budget_df[budget_df.month == budget_df.month.max()]
        for i, (_, row) in enumerate(latest.iterrows()):
            with cols[i % len(cols)]:
                pct = min(row['used_pct'], 100) / 100
                color = "🟢" if row['used_pct'] < 80 else ("🟡" if row['used_pct'] < 100 else "🔴")
                st.markdown(f"{color} **{row['category']}**")
                st.progress(min(pct, 1.0))
                st.caption(f"₹{row['spent']:,.0f} / ₹{row['budget']:,.0f} ({row['used_pct']:.0f}%)")
    else:
        st.info("No budgets set yet. Go to **Budget Manager** to create one.")

    # Anomalies
    anomalies = db.get_anomalies(user_id)
    if len(anomalies) > 0:
        st.subheader("🔍 Unusual Transactions Detected")
        st.warning(f"⚠️ **{len(anomalies)}** transaction(s) are over 3× their category average")
        anomalies['ratio'] = (anomalies['amount'] / anomalies['avg_amt']).round(1)
        st.dataframe(
            anomalies[['transaction_date', 'category', 'title', 'amount', 'ratio', 'wallet']]
            .rename(columns={
                'transaction_date': 'Date', 'category': 'Category', 'title': 'Title',
                'amount': 'Amount (₹)', 'ratio': 'x Avg', 'wallet': 'Payment'
            }),
            use_container_width=True
        )

    # Forecast
    if len(monthly) >= 3:
        st.subheader("🔮 Next Month Expense Forecast")
        monthly_exp = monthly[['month', 'expense']].copy()
        monthly_exp['t'] = range(len(monthly_exp))
        model = LinearRegression()
        model.fit(monthly_exp[['t']], monthly_exp['expense'])
        predicted = model.predict([[len(monthly_exp)]])[0]

        c1, c2 = st.columns(2)
        c1.metric("Predicted Next Month", f"₹{predicted:,.0f}",
                  delta=f"₹{predicted - monthly_exp['expense'].iloc[-1]:,.0f} vs last")
        c2.metric("12-Month Average", f"₹{monthly_exp['expense'].mean():,.0f}")
        st.caption("⚠️ Simple linear regression baseline.")


# ============================================================
# ADD TRANSACTION PAGE
# ============================================================
def show_add_transaction():
    user_id = st.session_state.user['user_id']
    st.markdown('<p class="main-header">➕ Add Transaction</p>', unsafe_allow_html=True)
    st.markdown("---")

    col1, col2 = st.columns([2, 1])

    with col1:
        with st.form("add_txn_form", clear_on_submit=True):
            txn_type = st.radio("Type", ["expense", "income"], horizontal=True,
                                format_func=lambda x: "💸 Expense" if x == "expense" else "💵 Income")

            categories = db.get_categories(user_id, txn_type)
            wallets = db.get_wallets(user_id)

            if not categories:
                st.warning("No categories found. Add categories first!")
                st.form_submit_button("Save", disabled=True)
                return
            if not wallets:
                st.warning("No wallets found. Add wallets first!")
                st.form_submit_button("Save", disabled=True)
                return

            cat_options = {c['name']: c['category_id'] for c in categories}
            wallet_options = {f"{w['name']} ({w['type']})": w['wallet_id'] for w in wallets}

            c1, c2 = st.columns(2)
            with c1:
                cat_name = st.selectbox("📁 Category", list(cat_options.keys()))
                amount = st.number_input("💰 Amount (₹)", min_value=1.0, step=100.0, value=100.0)
            with c2:
                wallet_name = st.selectbox("💳 Wallet / Payment", list(wallet_options.keys()))
                txn_date = st.date_input("📅 Date", value=date.today())

            title = st.text_input("📝 Title", placeholder="e.g., Grocery from BigBasket")
            description = st.text_area("📋 Description (optional)", placeholder="Any notes...",
                                       height=68)

            submitted = st.form_submit_button("💾 Save Transaction", use_container_width=True, type="primary")

            if submitted:
                success, msg = db.add_transaction(
                    user_id, cat_options[cat_name], wallet_options[wallet_name],
                    amount, txn_type, title, description, txn_date
                )
                if success:
                    st.success(msg)
                else:
                    st.error(msg)

    with col2:
        st.subheader("📊 Recent Activity")
        recent = db.get_transactions(user_id, limit=5)
        if len(recent) > 0:
            for _, r in recent.iterrows():
                icon = "💵" if r['type'] == 'income' else "💸"
                color = "#2ecc71" if r['type'] == 'income' else "#e74c3c"
                st.markdown(
                    f"{icon} **₹{r['amount']:,.0f}** — {r['category_name']}"
                    f"<br><span style='color:#888; font-size:0.8rem;'>"
                    f"{r['transaction_date']} · {r['wallet_name']}</span>",
                    unsafe_allow_html=True
                )
                st.markdown("---")
        else:
            st.info("No transactions yet.")

        # Wallet balances
        st.subheader("💳 Wallet Balances")
        wallets = db.get_wallets(user_id)
        for w in wallets:
            icon = {"cash": "💵", "bank": "🏦", "upi": "📱", "card": "💳"}.get(w['type'], "💰")
            st.metric(f"{icon} {w['name']}", f"₹{w['current_balance']:,.0f}")


# ============================================================
# MANAGE WALLETS PAGE
# ============================================================
def show_wallets():
    user_id = st.session_state.user['user_id']
    st.markdown('<p class="main-header">💳 Manage Wallets</p>', unsafe_allow_html=True)
    st.markdown("---")

    col1, col2 = st.columns([1, 2])

    with col1:
        st.subheader("➕ Add New Wallet")
        with st.form("add_wallet", clear_on_submit=True):
            name = st.text_input("Wallet Name", placeholder="e.g., HDFC Savings")
            w_type = st.selectbox("Type", ["bank", "upi", "cash", "card"],
                                  format_func=lambda x: {"bank": "🏦 Bank", "upi": "📱 UPI",
                                                          "cash": "💵 Cash", "card": "💳 Card"}[x])
            balance = st.number_input("Initial Balance (₹)", min_value=0.0, step=1000.0)
            if st.form_submit_button("Add Wallet", use_container_width=True, type="primary"):
                if name:
                    success, msg = db.add_wallet(user_id, name, w_type, balance)
                    if success:
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(msg)

    with col2:
        st.subheader("📋 Your Wallets")
        wallets = db.get_wallets(user_id)
        if wallets:
            for w in wallets:
                icon = {"cash": "💵", "bank": "🏦", "upi": "📱", "card": "💳"}.get(w['type'], "💰")
                c1, c2, c3 = st.columns([3, 2, 1])
                with c1:
                    st.markdown(f"### {icon} {w['name']}")
                    st.caption(f"Type: {w['type'].upper()}")
                with c2:
                    st.metric("Balance", f"₹{w['current_balance']:,.0f}")
                with c3:
                    if st.button("🗑️", key=f"del_w_{w['wallet_id']}", help="Delete wallet"):
                        success, msg = db.delete_wallet(w['wallet_id'])
                        if success:
                            st.rerun()
                        else:
                            st.error(msg)
                st.markdown("---")
        else:
            st.info("No wallets added yet.")


# ============================================================
# CATEGORIES PAGE
# ============================================================
def show_categories():
    user_id = st.session_state.user['user_id']
    st.markdown('<p class="main-header">📁 Categories</p>', unsafe_allow_html=True)
    st.markdown("---")

    col1, col2 = st.columns([1, 2])

    with col1:
        st.subheader("➕ Add Category")
        with st.form("add_cat", clear_on_submit=True):
            name = st.text_input("Category Name", placeholder="e.g., Subscriptions")
            cat_type = st.radio("Type", ["expense", "income"], horizontal=True)
            if st.form_submit_button("Add Category", use_container_width=True, type="primary"):
                if name:
                    success, msg = db.add_category(user_id, name, cat_type)
                    if success:
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(msg)

    with col2:
        st.subheader("📋 Your Categories")
        t1, t2 = st.tabs(["💸 Expense", "💵 Income"])

        with t1:
            cats = db.get_categories(user_id, 'expense')
            if cats:
                for c in cats:
                    c1, c2 = st.columns([4, 1])
                    c1.markdown(f"📂 {c['name']}")
                    if c2.button("🗑️", key=f"del_c_{c['category_id']}", help="Delete"):
                        db.delete_category(c['category_id'])
                        st.rerun()
            else:
                st.info("No expense categories.")

        with t2:
            cats = db.get_categories(user_id, 'income')
            if cats:
                for c in cats:
                    c1, c2 = st.columns([4, 1])
                    c1.markdown(f"📂 {c['name']}")
                    if c2.button("🗑️", key=f"del_ci_{c['category_id']}", help="Delete"):
                        db.delete_category(c['category_id'])
                        st.rerun()
            else:
                st.info("No income categories.")


# ============================================================
# BUDGET MANAGER PAGE
# ============================================================
def show_budget_manager():
    user_id = st.session_state.user['user_id']
    st.markdown('<p class="main-header">📋 Budget Manager</p>', unsafe_allow_html=True)
    st.markdown("---")

    col1, col2 = st.columns([1, 2])

    with col1:
        st.subheader("➕ Set Budget")
        with st.form("add_budget", clear_on_submit=True):
            cats = db.get_categories(user_id, 'expense')
            if not cats:
                st.warning("Add expense categories first!")
                st.form_submit_button("Set Budget", disabled=True)
                return

            cat_options = {c['name']: c['category_id'] for c in cats}
            cat_name = st.selectbox("Category", list(cat_options.keys()))
            amount = st.number_input("Monthly Budget (₹)", min_value=100.0, step=500.0, value=5000.0)
            period = st.selectbox("Period", ["monthly", "weekly"])

            today = date.today()
            c1, c2 = st.columns(2)
            with c1:
                start = st.date_input("Start Date", value=today.replace(day=1))
            with c2:
                # Default end = last day of month
                next_month = (today.replace(day=28) + timedelta(days=4))
                end_default = next_month.replace(day=1) - timedelta(days=1)
                end = st.date_input("End Date", value=end_default)

            if st.form_submit_button("Set Budget", use_container_width=True, type="primary"):
                success, msg = db.add_budget(user_id, cat_options[cat_name], amount, period, start, end)
                if success:
                    st.success(msg)
                    st.rerun()
                else:
                    st.error(msg)

    with col2:
        st.subheader("📊 Budget vs Actual")
        budget_df = db.get_budget_status(user_id)
        if len(budget_df) > 0:
            # Visual bars
            latest_month = budget_df['month'].max()
            latest = budget_df[budget_df.month == latest_month]

            fig = go.Figure()
            fig.add_trace(go.Bar(y=latest['category'], x=latest['budget'],
                                 name='Budget', orientation='h', marker_color='#3498db'))
            fig.add_trace(go.Bar(y=latest['category'], x=latest['spent'],
                                 name='Actual', orientation='h', marker_color='#e74c3c'))
            fig.update_layout(barmode='group', height=350, title=f'Budget vs Actual — {latest_month}',
                              xaxis_title='Amount (₹)')
            st.plotly_chart(fig, use_container_width=True)

            # Table
            over = budget_df[budget_df['used_pct'] > 100]
            if len(over) > 0:
                st.warning(f"🚨 **{len(over)}** over-budget!")
            st.dataframe(
                budget_df[['month', 'category', 'budget', 'spent', 'used_pct']]
                .sort_values('used_pct', ascending=False),
                use_container_width=True
            )

            # Delete buttons
            st.subheader("🗑️ Remove Budgets")
            for _, b in budget_df.iterrows():
                c1, c2 = st.columns([4, 1])
                c1.write(f"{b['category']} — {b['month']} (₹{b['budget']:,.0f})")
                if c2.button("🗑️", key=f"del_b_{b['budget_id']}"):
                    db.delete_budget(b['budget_id'])
                    st.rerun()
        else:
            st.info("No budgets set yet. Create one on the left!")


# ============================================================
# GOALS PAGE
# ============================================================
def show_goals():
    user_id = st.session_state.user['user_id']
    st.markdown('<p class="main-header">🎯 Goals</p>', unsafe_allow_html=True)
    st.markdown("---")

    col1, col2 = st.columns([1, 2])

    with col1:
        st.subheader("➕ Create Goal")
        with st.form("add_goal", clear_on_submit=True):
            name = st.text_input("Goal Name", placeholder="e.g., New Laptop")
            target = st.number_input("Target Amount (₹)", min_value=100.0, step=1000.0, value=50000.0)
            current = st.number_input("Already Saved (₹)", min_value=0.0, step=500.0, value=0.0)
            target_date = st.date_input("Target Date",
                                        value=date.today() + timedelta(days=180))
            desc = st.text_input("Description (optional)", placeholder="Why this goal?")

            if st.form_submit_button("Create Goal", use_container_width=True, type="primary"):
                if name:
                    success, msg = db.add_goal(user_id, name, target, current, target_date, desc)
                    if success:
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(msg)

    with col2:
        st.subheader("📋 Your Goals")
        goals_df = db.get_goals(user_id)

        if len(goals_df) > 0:
            active = goals_df[goals_df.status == 'active']
            completed = goals_df[goals_df.status == 'completed']

            if len(active) > 0:
                for _, g in active.iterrows():
                    progress = g['current_amount'] / g['target_amount'] if g['target_amount'] > 0 else 0
                    days_left = (pd.to_datetime(g['target_date']) - pd.Timestamp.now()).days

                    c1, c2, c3 = st.columns([3, 2, 1])
                    with c1:
                        st.markdown(f"### 🎯 {g['name']}")
                        st.progress(min(progress, 1.0))
                        st.caption(
                            f"₹{g['current_amount']:,.0f} / ₹{g['target_amount']:,.0f} "
                            f"({progress*100:.1f}%) — {max(days_left, 0)} days left"
                        )
                        if days_left > 0:
                            remaining = g['target_amount'] - g['current_amount']
                            monthly = remaining / max(days_left / 30, 1)
                            st.caption(f"💡 Need ₹{monthly:,.0f}/month to reach goal")
                    with c2:
                        new_amt = st.number_input(
                            "Update saved ₹", value=float(g['current_amount']),
                            min_value=0.0, step=500.0, key=f"goal_amt_{g['goal_id']}"
                        )
                        if st.button("💾 Update", key=f"upd_g_{g['goal_id']}"):
                            db.update_goal_amount(g['goal_id'], new_amt)
                            st.rerun()
                    with c3:
                        if st.button("🗑️", key=f"del_g_{g['goal_id']}", help="Delete goal"):
                            db.delete_goal(g['goal_id'])
                            st.rerun()
                    st.markdown("---")

            if len(completed) > 0:
                st.subheader("✅ Completed Goals")
                for _, g in completed.iterrows():
                    st.markdown(f"✅ ~~{g['name']}~~ — ₹{g['target_amount']:,.0f} achieved!")
        else:
            st.info("No goals yet. Create one on the left!")


# ============================================================
# ALL TRANSACTIONS PAGE
# ============================================================
def show_all_transactions():
    user_id = st.session_state.user['user_id']
    st.markdown('<p class="main-header">📜 All Transactions</p>', unsafe_allow_html=True)
    st.markdown("---")

    txns = db.get_transactions(user_id)

    if len(txns) == 0:
        st.info("No transactions yet. Go add some!")
        return

    # Filters
    c1, c2, c3 = st.columns(3)
    with c1:
        type_filter = st.selectbox("Type", ["All", "income", "expense"])
    with c2:
        cats = sorted(txns['category_name'].unique())
        cat_filter = st.multiselect("Categories", cats, default=cats)
    with c3:
        date_range = st.date_input("Date Range",
                                   value=(pd.to_datetime(txns['transaction_date'].min()).date(),
                                          date.today()),
                                   key="date_range_filter")

    # Apply filters
    filtered = txns.copy()
    if type_filter != "All":
        filtered = filtered[filtered.type == type_filter]
    if cat_filter:
        filtered = filtered[filtered.category_name.isin(cat_filter)]
    if len(date_range) == 2:
        filtered = filtered[
            (pd.to_datetime(filtered.transaction_date).dt.date >= date_range[0]) &
            (pd.to_datetime(filtered.transaction_date).dt.date <= date_range[1])
        ]

    # Summary
    c1, c2, c3 = st.columns(3)
    inc = filtered[filtered.type == 'income']['amount'].sum()
    exp = filtered[filtered.type == 'expense']['amount'].sum()
    c1.metric("Income (filtered)", f"₹{inc:,.0f}")
    c2.metric("Expense (filtered)", f"₹{exp:,.0f}")
    c3.metric("Count", f"{len(filtered)}")

    # Table with delete
    st.markdown("---")

    display_df = filtered[['transaction_date', 'type', 'category_name', 'title',
                            'amount', 'wallet_name', 'transaction_id']].copy()
    display_df.columns = ['Date', 'Type', 'Category', 'Title', 'Amount (₹)', 'Payment', 'ID']

    # Show with colored type
    st.dataframe(display_df.drop(columns=['ID']), use_container_width=True, height=400)

    # Delete section
    st.subheader("🗑️ Delete a Transaction")
    if len(filtered) > 0:
        txn_options = {
            f"#{r['transaction_id']} | {r['transaction_date']} | {r['category_name']} | ₹{r['amount']:,.0f}": r['transaction_id']
            for _, r in filtered.head(50).iterrows()
        }
        selected_txn = st.selectbox("Select transaction to delete", list(txn_options.keys()))
        if st.button("🗑️ Delete Selected", type="secondary"):
            success, msg = db.delete_transaction(txn_options[selected_txn], user_id)
            if success:
                st.success(msg)
                st.rerun()
            else:
                st.error(msg)


# ============================================================
# MAIN APP ROUTER
# ============================================================
if not st.session_state.logged_in:
    show_auth_page()
else:
    page = show_sidebar()

    if page == "📊 Dashboard":
        show_dashboard()
    elif page == "➕ Add Transaction":
        show_add_transaction()
    elif page == "💳 Manage Wallets":
        show_wallets()
    elif page == "📁 Categories":
        show_categories()
    elif page == "📋 Budget Manager":
        show_budget_manager()
    elif page == "🎯 Goals":
        show_goals()
    elif page == "📜 All Transactions":
        show_all_transactions()

    # Footer
    st.markdown("---")
    st.markdown(
        '<div style="text-align:center; color:#888;">'
        '💰 Money Mate Analytics | Built with Streamlit & Plotly | '
        '<a href="https://github.com/codeknight2531-bit/money-mate-analytics" target="_blank">GitHub</a>'
        '</div>',
        unsafe_allow_html=True
    )

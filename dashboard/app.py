"""
Money Mate: Personal Finance Analytics Dashboard
Dual-Mode Application:
- 🎮 Demo Mode: Explore 12 months of rich analytics & 1,900+ transactions without signing in
- 👤 Real Mode: Live authenticated personal finance manager (SQLite CRUD + Auth)
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

# Add dashboard dir to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import database as db
import demo_data as demo

# --- Page Config ---
st.set_page_config(
    page_title='💰 Money Mate Analytics',
    page_icon='💰',
    layout='wide',
    initial_sidebar_state='expanded'
)

# --- Custom Styling ---
st.markdown("""
<style>
    .main-header {
        font-size: 2.3rem;
        font-weight: 800;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0;
    }
    .sub-header { font-size: 1.05rem; color: #888; margin-top: -8px; }
    .mode-badge-demo {
        display: inline-block;
        background: #f39c1222;
        color: #f39c12;
        border: 1px solid #f39c12;
        padding: 4px 12px;
        border-radius: 20px;
        font-weight: 600;
        font-size: 0.85rem;
        margin-bottom: 12px;
    }
    .mode-badge-real {
        display: inline-block;
        background: #2ecc7122;
        color: #2ecc71;
        border: 1px solid #2ecc71;
        padding: 4px 12px;
        border-radius: 20px;
        font-weight: 600;
        font-size: 0.85rem;
        margin-bottom: 12px;
    }
</style>
""", unsafe_allow_html=True)

# --- Session State Initialization ---
if 'app_mode' not in st.session_state:
    st.session_state.app_mode = "demo"  # Default to demo for immediate rich showcase
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'user' not in st.session_state:
    st.session_state.user = None
if 'demo_user_id' not in st.session_state:
    st.session_state.demo_user_id = 1


# ============================================================
# SIDEBAR MODE SWITCHER (Always Visible)
# ============================================================
def render_sidebar():
    """Renders the sidebar with mode switching and mode-specific controls."""
    st.sidebar.markdown("### 🔀 Workspace Mode")
    
    mode_options = ["🎮 Demo Mode (Sample Data)", "👤 Real Mode (Live Account)"]
    selected_mode_idx = 0 if st.session_state.app_mode == "demo" else 1
    
    selected_mode = st.sidebar.radio(
        "Choose Mode:",
        mode_options,
        index=selected_mode_idx,
        label_visibility="collapsed"
    )
    
    # Check if mode switched
    new_mode = "demo" if "Demo Mode" in selected_mode else "real"
    if new_mode != st.session_state.app_mode:
        st.session_state.app_mode = new_mode
        st.rerun()

    st.sidebar.markdown("---")

    # ----------------------------------------------------
    # DEMO MODE SIDEBAR CONTROLS
    # ----------------------------------------------------
    if st.session_state.app_mode == "demo":
        st.sidebar.markdown("### 🎭 Demo Persona")
        persona_map = {
            "Aarav Sharma (Tech Pro, ₹30k)": 1,
            "Riya Patel (UX Designer, ₹35k)": 2,
            "Kabir Verma (Product Lead, ₹40k)": 3
        }
        current_name = [k for k, v in persona_map.items() if v == st.session_state.demo_user_id][0]
        selected_persona = st.sidebar.selectbox("Select Profile", list(persona_map.keys()), 
                                                index=list(persona_map.keys()).index(current_name))
        if persona_map[selected_persona] != st.session_state.demo_user_id:
            st.session_state.demo_user_id = persona_map[selected_persona]
            st.rerun()

        # Month Filters for Demo Data
        tx, _, _, _, _, _ = demo.load_demo_bundle()
        all_months = sorted(tx[tx.user_id == st.session_state.demo_user_id]['month'].unique().tolist())
        st.sidebar.markdown("### 📅 Filter Months")
        selected_months = st.sidebar.multiselect(
            "Months", all_months, default=all_months, label_visibility="collapsed"
        )
        if not selected_months:
            selected_months = all_months

        st.sidebar.markdown("---")
        demo_page = st.sidebar.radio(
            "📂 Demo Navigation",
            ["📊 Analytics Overview", "📋 Budget Tracker", "🔍 Behavior & Anomalies", 
             "🎯 Goals & Forecast", "📜 Browse Transactions"]
        )
        
        st.sidebar.markdown("---")
        st.sidebar.info("💡 Want to track your real expenses? Switch to **Real Mode** above!")
        return demo_page, selected_months

    # ----------------------------------------------------
    # REAL MODE SIDEBAR CONTROLS
    # ----------------------------------------------------
    else:
        if not st.session_state.logged_in:
            st.sidebar.warning("🔒 Please login or register to access Real Mode.")
            st.sidebar.markdown("---")
            if st.sidebar.button("🚀 Switch back to Demo Mode", use_container_width=True):
                st.session_state.app_mode = "demo"
                st.rerun()
            return None, None
        else:
            user = st.session_state.user
            st.sidebar.markdown(f"### 👋 Hello, {user['name']}!")
            st.sidebar.caption(f"📧 {user['email']}")
            st.sidebar.markdown("---")

            real_page = st.sidebar.radio(
                "📂 Live Navigation",
                ["📊 Dashboard", "➕ Add Transaction", "💳 Manage Wallets",
                 "📁 Categories", "📋 Budget Manager", "🎯 Goals", "📜 All Transactions"]
            )

            st.sidebar.markdown("---")
            # Quick Helper: Seed sample data
            with st.sidebar.expander("⚡ Starter Tools"):
                st.caption("Quickly populate this account with 100+ sample transactions to test features.")
                if st.button("📥 Load Sample Data", use_container_width=True):
                    ok, msg = db.seed_user_sample_data(user['user_id'])
                    if ok:
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(msg)

            if st.sidebar.button("🚪 Logout", use_container_width=True):
                st.session_state.logged_in = False
                st.session_state.user = None
                st.session_state.app_mode = "demo"
                st.rerun()

            return real_page, None


# ============================================================
# DEMO MODE PAGES
# ============================================================
def show_demo_overview(user_id, selected_months):
    st.markdown('<div class="mode-badge-demo">🎮 DEMO MODE ACTIVE</div>', unsafe_allow_html=True)
    st.markdown('<p class="main-header">📊 Personal Finance Analytics (Demo)</p>', unsafe_allow_html=True)
    persona = demo.DEMO_USERS.get(user_id, {"name": "User", "role": "Demo"})
    st.markdown(f'<p class="sub-header">Profile: <b>{persona["name"]}</b> ({persona["role"]} · {persona["salary"]})</p>', unsafe_allow_html=True)
    st.markdown("---")

    monthly = demo.get_demo_monthly_summary(user_id, selected_months)
    inc = monthly['income'].sum()
    exp = monthly['expense'].sum()
    savings = inc - exp
    savings_rate = (savings / inc * 100) if inc > 0 else 0
    txns = demo.get_demo_transactions(user_id, selected_months=selected_months)

    # 4 KPI Cards
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("💵 Total Income", f"₹{inc:,.0f}")
    c2.metric("💸 Total Expense", f"₹{exp:,.0f}")
    c3.metric("🏦 Net Savings", f"₹{savings:,.0f}", delta=f"{savings_rate:.1f}% rate")
    c4.metric("📝 Transactions", f"{len(txns):,}")

    st.markdown("---")

    # Monthly Bar Chart + Category Donut
    col1, col2 = st.columns([3, 2])
    with col1:
        st.subheader("📈 Monthly Income vs Expense")
        fig = go.Figure()
        fig.add_trace(go.Bar(x=monthly['month'], y=monthly['income'], name='Income', marker_color='#2ecc71'))
        fig.add_trace(go.Bar(x=monthly['month'], y=monthly['expense'], name='Expense', marker_color='#e74c3c'))
        fig.update_layout(barmode='group', height=400, xaxis_title='Month', yaxis_title='Amount (₹)',
                          legend=dict(orientation="h", yanchor="bottom", y=1.02))
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("🍩 Spending by Category")
        cat_df = demo.get_demo_category_spend(user_id, selected_months)
        if len(cat_df) > 0:
            fig2 = px.pie(cat_df, values='spend', names='category',
                          color_discrete_sequence=px.colors.qualitative.Set3, hole=0.4)
            fig2.update_traces(textposition='inside', textinfo='percent+label')
            fig2.update_layout(height=400, showlegend=False)
            st.plotly_chart(fig2, use_container_width=True)

    # Savings Rate Trend
    st.subheader("📉 Savings Rate Trend")
    if len(monthly) > 0:
        monthly['rate'] = ((monthly['income'] - monthly['expense']) / monthly['income'] * 100).round(1)
        fig3 = go.Figure()
        fig3.add_trace(go.Scatter(
            x=monthly['month'], y=monthly['rate'], mode='lines+markers+text',
            text=monthly['rate'].astype(str) + '%', textposition='top center',
            line=dict(color='#3498db', width=3), marker=dict(size=9)
        ))
        fig3.add_hline(y=20, line_dash="dash", line_color="green", annotation_text="20% Target")
        fig3.update_layout(height=350, yaxis_title='Savings Rate (%)', xaxis_title='Month')
        st.plotly_chart(fig3, use_container_width=True)


def show_demo_budgets(user_id, selected_months):
    st.markdown('<div class="mode-badge-demo">🎮 DEMO MODE ACTIVE</div>', unsafe_allow_html=True)
    st.markdown('<p class="main-header">📋 Budget Adherence & Tracking (Demo)</p>', unsafe_allow_html=True)
    st.markdown("---")

    b_df = demo.get_demo_budget_status(user_id, selected_months)
    if len(b_df) > 0:
        over = b_df[b_df['used_pct'] > 100]
        c1, c2, c3 = st.columns(3)
        c1.metric("🔴 Over-Budget Counts", len(over))
        c2.metric("📊 Total Budgets Tracked", len(b_df))
        c3.metric("⚡ Max Overshoot", f"{over['used_pct'].max():.0f}%" if len(over) > 0 else "None")

        st.markdown("---")
        latest_month = b_df['month'].max()
        latest = b_df[b_df.month == latest_month]

        fig = go.Figure()
        fig.add_trace(go.Bar(y=latest['category'], x=latest['budget'], name='Budget', orientation='h', marker_color='#3498db'))
        fig.add_trace(go.Bar(y=latest['category'], x=latest['spent'], name='Actual Spent', orientation='h', marker_color='#e74c3c'))
        fig.update_layout(title=f'Budget vs Actual — {latest_month}', barmode='group', height=400, xaxis_title='Amount (₹)')
        st.plotly_chart(fig, use_container_width=True)

        st.subheader("🚨 Over-Budget Alert Table")
        if len(over) > 0:
            st.dataframe(
                over[['month', 'category', 'budget', 'spent', 'used_pct']]
                .sort_values('used_pct', ascending=False)
                .style.format({'budget': '₹{:,.0f}', 'spent': '₹{:,.0f}', 'used_pct': '{:.1f}%'}),
                use_container_width=True
            )
        else:
            st.success("✅ All categories stayed within budget!")


def show_demo_behavior(user_id, selected_months):
    st.markdown('<div class="mode-badge-demo">🎮 DEMO MODE ACTIVE</div>', unsafe_allow_html=True)
    st.markdown('<p class="main-header">🔍 Payment Behavior & Anomaly Detection (Demo)</p>', unsafe_allow_html=True)
    st.markdown("---")

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("💳 Payment Method Distribution")
        w_df = demo.get_demo_wallet_usage(user_id, selected_months)
        fig = px.bar(w_df, x='wallet', y='spend', color='wallet', text='txn_count',
                     color_discrete_sequence=px.colors.qualitative.Pastel)
        fig.update_traces(texttemplate='%{text} txns', textposition='outside')
        fig.update_layout(height=400, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("📅 Weekday Spending Breakdown")
        txns = demo.get_demo_transactions(user_id, selected_months=selected_months)
        exp_tx = txns[txns.type == 'expense']
        day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        day_df = exp_tx.groupby('weekday')['amount'].mean().reindex(day_order).reset_index()
        fig2 = px.bar(day_df, x='weekday', y='amount', color='amount', color_continuous_scale='Viridis',
                      labels={'amount': 'Avg Spend (₹)', 'weekday': 'Day of Week'})
        fig2.update_layout(height=400, coloraxis_showscale=False)
        st.plotly_chart(fig2, use_container_width=True)

    st.markdown("---")
    st.subheader("🚨 Anomalous Spending (> 3× Category Average)")
    anomalies = demo.get_demo_anomalies(user_id)
    if len(anomalies) > 0:
        st.warning(f"⚠️ Detected **{len(anomalies)}** statistically unusual transactions.")
        st.dataframe(
            anomalies.rename(columns={
                'transaction_date': 'Date', 'category': 'Category', 'title': 'Title',
                'amount': 'Amount (₹)', 'ratio': 'Multiple (x)', 'wallet': 'Payment Method'
            }).style.format({'Amount (₹)': '₹{:,.0f}', 'avg_amt': '₹{:,.0f}'}),
            use_container_width=True
        )


def show_demo_goals_forecast(user_id, selected_months):
    st.markdown('<div class="mode-badge-demo">🎮 DEMO MODE ACTIVE</div>', unsafe_allow_html=True)
    st.markdown('<p class="main-header">🎯 Financial Goals & Machine Learning Forecast (Demo)</p>', unsafe_allow_html=True)
    st.markdown("---")

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("🎯 Active Savings Goals")
        goals_df = demo.get_demo_goals(user_id)
        for _, g in goals_df.iterrows():
            pct = g['current_amount'] / g['target_amount'] if g['target_amount'] > 0 else 0
            st.markdown(f"**{g['name']}**")
            st.progress(min(pct, 1.0))
            st.caption(f"₹{g['current_amount']:,.0f} / ₹{g['target_amount']:,.0f} ({pct*100:.1f}%) · Target: {g['target_date']}")
            st.markdown("---")

    with col2:
        st.subheader("🔮 Next-Month Linear Expense Forecast")
        monthly = demo.get_demo_monthly_summary(user_id, selected_months)
        if len(monthly) >= 3:
            monthly['t'] = range(len(monthly))
            model = LinearRegression().fit(monthly[['t']], monthly['expense'])
            next_exp = model.predict([[len(monthly)]])[0]

            st.metric("Expected Next Month Spend", f"₹{next_exp:,.0f}",
                      delta=f"₹{next_exp - monthly['expense'].iloc[-1]:,.0f} vs last month")
            st.metric("12-Month Expense Average", f"₹{monthly['expense'].mean():,.0f}")

            fig = go.Figure()
            fig.add_trace(go.Scatter(x=monthly['month'], y=monthly['expense'], mode='lines+markers', name='Historical'))
            fig.add_trace(go.Scatter(x=['Next'], y=[next_exp], mode='markers', name='Predicted', marker=dict(size=14, color='orange')))
            fig.update_layout(height=300, title='Expense Trajectory')
            st.plotly_chart(fig, use_container_width=True)


def show_demo_transactions(user_id, selected_months):
    st.markdown('<div class="mode-badge-demo">🎮 DEMO MODE ACTIVE</div>', unsafe_allow_html=True)
    st.markdown('<p class="main-header">📜 Browse Demo Transactions</p>', unsafe_allow_html=True)
    st.markdown("---")

    txns = demo.get_demo_transactions(user_id, selected_months=selected_months)
    st.caption(f"Showing {len(txns)} records from the 1,900+ synthetic dataset.")
    
    display_cols = ['transaction_date', 'type', 'category_name', 'title', 'amount', 'wallet_name']
    st.dataframe(
        txns[display_cols].rename(columns={
            'transaction_date': 'Date', 'type': 'Type', 'category_name': 'Category',
            'title': 'Description', 'amount': 'Amount (₹)', 'wallet_name': 'Payment Method'
        }).style.format({'Amount (₹)': '₹{:,.0f}'}),
        use_container_width=True, height=500
    )


# ============================================================
# REAL MODE: AUTHENTICATION PAGE
# ============================================================
def show_auth_page():
    """Show login/signup page for Real Mode."""
    st.markdown('<div class="mode-badge-real">👤 REAL MODE (LIVE DATABASE)</div>', unsafe_allow_html=True)
    
    col_spacer1, col_main, col_spacer2 = st.columns([1, 2, 1])
    with col_main:
        st.markdown('<p class="main-header">💰 Money Mate</p>', unsafe_allow_html=True)
        st.markdown('<p class="sub-header">Personal Finance Account · Isolated & Secure</p>', unsafe_allow_html=True)
        
        # Demo Banner in Auth Page
        st.markdown("""
        <div style="background: linear-gradient(135deg, #667eea18, #764ba218); padding: 15px; border-radius: 10px; border-left: 4px solid #667eea; margin: 15px 0;">
            <b style="color: #667eea;">✨ Just exploring?</b><br>
            <span style="font-size: 0.9rem; color: #aaa;">You can preview the full dashboard with 1,900+ sample transactions without signing up.</span>
        </div>
        """, unsafe_allow_html=True)
        if st.button("🚀 Switch to Demo Mode", use_container_width=True):
            st.session_state.app_mode = "demo"
            st.rerun()

        st.markdown("---")
        tab_login, tab_signup = st.tabs(["🔐 Login", "📝 Sign Up"])

        with tab_login:
            with st.form("login_form"):
                st.subheader("Login to Your Account")
                email = st.text_input("📧 Email", placeholder="you@example.com")
                password = st.text_input("🔑 Password", type="password", placeholder="Enter password")
                submit = st.form_submit_button("Login", use_container_width=True, type="primary")

                if submit:
                    if not email or not password:
                        st.error("Please fill in both email and password.")
                    else:
                        success, result = db.login_user(email, password)
                        if success:
                            st.session_state.logged_in = True
                            st.session_state.user = result
                            st.session_state.app_mode = "real"
                            st.rerun()
                        else:
                            st.error(result)

        with tab_signup:
            with st.form("signup_form"):
                st.subheader("Create a New Account")
                name = st.text_input("👤 Full Name", placeholder="e.g. Rahul Verma")
                email = st.text_input("📧 Email", placeholder="you@example.com", key="reg_email")
                phone = st.text_input("📱 Phone (optional)", placeholder="+91 9876543210")
                p1 = st.text_input("🔑 Password", type="password", placeholder="Min 6 characters", key="reg_p1")
                p2 = st.text_input("🔑 Confirm Password", type="password", placeholder="Repeat password")
                submit = st.form_submit_button("Register Account", use_container_width=True, type="primary")

                if submit:
                    if not name or not email or not p1:
                        st.error("Please fill in all required fields.")
                    elif len(p1) < 6:
                        st.error("Password must be at least 6 characters.")
                    elif p1 != p2:
                        st.error("Passwords do not match.")
                    else:
                        ok, msg = db.register_user(name, email, p1, phone)
                        if ok:
                            st.success(msg + " You can now login.")
                        else:
                            st.error(msg)


# ============================================================
# REAL MODE: CRUD & ANALYTICS PAGES
# ============================================================
def show_real_dashboard():
    user = st.session_state.user
    st.markdown('<div class="mode-badge-real">🟢 REAL MODE · LIVE DATA</div>', unsafe_allow_html=True)
    st.markdown(f'<p class="main-header">📊 Dashboard: {user["name"]}</p>', unsafe_allow_html=True)
    st.markdown("---")

    monthly = db.get_monthly_summary(user['user_id'])
    if len(monthly) == 0:
        st.info("👋 **Welcome to your personal account!** You haven't added any transactions yet.")
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("""
            **How to get started:**
            1. ➕ Go to **Add Transaction** to record real expenses/income.
            2. 💳 Check **Manage Wallets** to add your bank, UPI, or cards.
            3. 📋 Set monthly **Budgets** to prevent overspending.
            """)
        with c2:
            st.markdown("""
            **Want instant sample data to test?**
            Click below to populate this account with 100+ sample transactions, budgets, and goals:
            """)
            if st.button("📥 Load Sample Data into My Account", type="primary"):
                ok, msg = db.seed_user_sample_data(user['user_id'])
                if ok:
                    st.success(msg)
                    st.rerun()
                else:
                    st.error(msg)
        return

    inc = monthly['income'].sum()
    exp = monthly['expense'].sum()
    savings = inc - exp
    savings_rate = (savings / inc * 100) if inc > 0 else 0
    txns = db.get_transactions(user['user_id'])

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("💵 Total Income", f"₹{inc:,.0f}")
    c2.metric("💸 Total Expense", f"₹{exp:,.0f}")
    c3.metric("🏦 Net Savings", f"₹{savings:,.0f}", delta=f"{savings_rate:.1f}% rate")
    c4.metric("📝 Transactions", f"{len(txns):,}")

    st.markdown("---")
    col1, col2 = st.columns([3, 2])
    with col1:
        st.subheader("📈 Monthly Income vs Expense")
        fig = go.Figure()
        fig.add_trace(go.Bar(x=monthly['month'], y=monthly['income'], name='Income', marker_color='#2ecc71'))
        fig.add_trace(go.Bar(x=monthly['month'], y=monthly['expense'], name='Expense', marker_color='#e74c3c'))
        fig.update_layout(barmode='group', height=400, xaxis_title='Month', yaxis_title='Amount (₹)')
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("🍩 Spending by Category")
        cat_df = db.get_category_spend(user['user_id'])
        if len(cat_df) > 0:
            fig2 = px.pie(cat_df, values='spend', names='category', hole=0.4,
                          color_discrete_sequence=px.colors.qualitative.Set3)
            fig2.update_layout(height=400, showlegend=False)
            st.plotly_chart(fig2, use_container_width=True)

    # Budget Status
    st.subheader("📋 Budget Adherence")
    b_df = db.get_budget_status(user['user_id'])
    if len(b_df) > 0:
        latest = b_df[b_df.month == b_df.month.max()]
        cols = st.columns(min(len(latest), 4))
        for i, (_, row) in enumerate(latest.iterrows()):
            with cols[i % len(cols)]:
                pct = min(row['used_pct'], 100) / 100
                st.markdown(f"**{row['category']}**")
                st.progress(pct)
                st.caption(f"₹{row['spent']:,.0f} / ₹{row['budget']:,.0f} ({row['used_pct']:.0f}%)")
    else:
        st.info("No budgets configured yet. Add one in **Budget Manager**.")


def show_real_add_transaction():
    user_id = st.session_state.user['user_id']
    st.markdown('<div class="mode-badge-real">🟢 REAL MODE</div>', unsafe_allow_html=True)
    st.markdown('<p class="main-header">➕ Add Transaction</p>', unsafe_allow_html=True)
    st.markdown("---")

    col1, col2 = st.columns([2, 1])
    with col1:
        with st.form("add_txn_form", clear_on_submit=True):
            txn_type = st.radio("Type", ["expense", "income"], horizontal=True,
                                format_func=lambda x: "💸 Expense" if x == "expense" else "💵 Income")
            categories = db.get_categories(user_id, txn_type)
            wallets = db.get_wallets(user_id)

            if not categories or not wallets:
                st.warning("Please ensure at least one category and wallet exist.")
                st.form_submit_button("Save", disabled=True)
                return

            cat_map = {c['name']: c['category_id'] for c in categories}
            wal_map = {f"{w['name']} ({w['type']})": w['wallet_id'] for w in wallets}

            c1, c2 = st.columns(2)
            with c1:
                cat_name = st.selectbox("Category", list(cat_map.keys()))
                amount = st.number_input("Amount (₹)", min_value=1.0, step=100.0, value=250.0)
            with c2:
                wal_name = st.selectbox("Wallet", list(wal_map.keys()))
                txn_date = st.date_input("Date", value=date.today())

            title = st.text_input("Title", placeholder="e.g. Grocery Store, Dinner, Electric Bill")
            desc = st.text_area("Notes", placeholder="Optional details...", height=68)

            if st.form_submit_button("💾 Save Transaction", type="primary", use_container_width=True):
                ok, msg = db.add_transaction(
                    user_id, cat_map[cat_name], wal_map[wal_name],
                    amount, txn_type, title, desc, txn_date
                )
                if ok:
                    st.success(msg)
                else:
                    st.error(msg)

    with col2:
        st.subheader("💳 Wallet Balances")
        wallets = db.get_wallets(user_id)
        for w in wallets:
            icon = {"cash": "💵", "bank": "🏦", "upi": "📱", "card": "💳"}.get(w['type'], "💰")
            st.metric(f"{icon} {w['name']}", f"₹{w['current_balance']:,.0f}")


def show_real_wallets():
    user_id = st.session_state.user['user_id']
    st.markdown('<div class="mode-badge-real">🟢 REAL MODE</div>', unsafe_allow_html=True)
    st.markdown('<p class="main-header">💳 Manage Wallets</p>', unsafe_allow_html=True)
    st.markdown("---")

    col1, col2 = st.columns([1, 2])
    with col1:
        st.subheader("➕ New Wallet")
        with st.form("new_w_form", clear_on_submit=True):
            name = st.text_input("Wallet Name", placeholder="e.g. Axis Bank, Paytm UPI")
            w_type = st.selectbox("Type", ["bank", "upi", "cash", "card"])
            bal = st.number_input("Starting Balance (₹)", min_value=0.0, step=1000.0, value=5000.0)
            if st.form_submit_button("Add Wallet", type="primary", use_container_width=True):
                if name:
                    ok, msg = db.add_wallet(user_id, name, w_type, bal)
                    if ok:
                        st.success(msg)
                        st.rerun()

    with col2:
        st.subheader("📋 Active Wallets")
        wallets = db.get_wallets(user_id)
        for w in wallets:
            c1, c2, c3 = st.columns([3, 2, 1])
            c1.markdown(f"**{w['name']}** ({w['type'].upper()})")
            c2.metric("Balance", f"₹{w['current_balance']:,.0f}")
            if c3.button("🗑️", key=f"delw_{w['wallet_id']}"):
                db.delete_wallet(w['wallet_id'])
                st.rerun()
            st.markdown("---")


def show_real_categories():
    user_id = st.session_state.user['user_id']
    st.markdown('<div class="mode-badge-real">🟢 REAL MODE</div>', unsafe_allow_html=True)
    st.markdown('<p class="main-header">📁 Categories</p>', unsafe_allow_html=True)
    st.markdown("---")

    col1, col2 = st.columns([1, 2])
    with col1:
        st.subheader("➕ Add Category")
        with st.form("new_c_form", clear_on_submit=True):
            name = st.text_input("Name", placeholder="e.g. Pet Care, OTT Subscriptions")
            ctype = st.radio("Type", ["expense", "income"], horizontal=True)
            if st.form_submit_button("Add Category", type="primary", use_container_width=True):
                if name:
                    ok, msg = db.add_category(user_id, name, ctype)
                    if ok:
                        st.success(msg)
                        st.rerun()

    with col2:
        t1, t2 = st.tabs(["💸 Expense", "💵 Income"])
        with t1:
            for c in db.get_categories(user_id, 'expense'):
                c1, c2 = st.columns([4, 1])
                c1.write(f"📂 {c['name']}")
                if c2.button("🗑️", key=f"del_ce_{c['category_id']}"):
                    db.delete_category(c['category_id'])
                    st.rerun()
        with t2:
            for c in db.get_categories(user_id, 'income'):
                c1, c2 = st.columns([4, 1])
                c1.write(f"📂 {c['name']}")
                if c2.button("🗑️", key=f"del_ci_{c['category_id']}"):
                    db.delete_category(c['category_id'])
                    st.rerun()


def show_real_budgets():
    user_id = st.session_state.user['user_id']
    st.markdown('<div class="mode-badge-real">🟢 REAL MODE</div>', unsafe_allow_html=True)
    st.markdown('<p class="main-header">📋 Budget Manager</p>', unsafe_allow_html=True)
    st.markdown("---")

    col1, col2 = st.columns([1, 2])
    with col1:
        st.subheader("➕ Set Monthly Budget")
        cats = db.get_categories(user_id, 'expense')
        if not cats:
            st.info("Add expense categories first.")
            return

        cat_map = {c['name']: c['category_id'] for c in cats}
        with st.form("budget_form", clear_on_submit=True):
            cname = st.selectbox("Category", list(cat_map.keys()))
            amt = st.number_input("Monthly Limit (₹)", min_value=100.0, step=500.0, value=5000.0)
            c1, c2 = st.columns(2)
            today = date.today()
            s_date = c1.date_input("Start", value=today.replace(day=1))
            e_date = c2.date_input("End", value=(today.replace(day=28) + timedelta(days=4)).replace(day=1) - timedelta(days=1))

            if st.form_submit_button("Set Budget", type="primary", use_container_width=True):
                ok, msg = db.add_budget(user_id, cat_map[cname], amt, 'monthly', s_date, e_date)
                if ok:
                    st.success(msg)
                    st.rerun()

    with col2:
        st.subheader("📊 Active Budgets")
        b_df = db.get_budget_status(user_id)
        if len(b_df) > 0:
            st.dataframe(b_df[['month', 'category', 'budget', 'spent', 'used_pct']], use_container_width=True)
            for _, b in b_df.iterrows():
                c1, c2 = st.columns([4, 1])
                c1.caption(f"{b['category']} ({b['month']}) — ₹{b['spent']:,.0f} / ₹{b['budget']:,.0f}")
                if c2.button("🗑️", key=f"delb_{b['budget_id']}"):
                    db.delete_budget(b['budget_id'])
                    st.rerun()
        else:
            st.info("No budgets created yet.")


def show_real_goals():
    user_id = st.session_state.user['user_id']
    st.markdown('<div class="mode-badge-real">🟢 REAL MODE</div>', unsafe_allow_html=True)
    st.markdown('<p class="main-header">🎯 Savings Goals</p>', unsafe_allow_html=True)
    st.markdown("---")

    col1, col2 = st.columns([1, 2])
    with col1:
        st.subheader("➕ New Goal")
        with st.form("goal_form", clear_on_submit=True):
            name = st.text_input("Goal Name", placeholder="e.g. Vacation, Bike, Emergency")
            target = st.number_input("Target Amount (₹)", min_value=100.0, step=1000.0, value=50000.0)
            current = st.number_input("Current Savings (₹)", min_value=0.0, step=500.0, value=5000.0)
            t_date = st.date_input("Target Date", value=date.today() + timedelta(days=180))
            if st.form_submit_button("Create Goal", type="primary", use_container_width=True):
                if name:
                    ok, msg = db.add_goal(user_id, name, target, current, t_date)
                    if ok:
                        st.success(msg)
                        st.rerun()

    with col2:
        st.subheader("📋 Goal Progress")
        g_df = db.get_goals(user_id)
        if len(g_df) > 0:
            for _, g in g_df.iterrows():
                pct = g['current_amount'] / g['target_amount'] if g['target_amount'] > 0 else 0
                c1, c2, c3 = st.columns([3, 2, 1])
                with c1:
                    st.markdown(f"**{g['name']}**")
                    st.progress(min(pct, 1.0))
                    st.caption(f"₹{g['current_amount']:,.0f} / ₹{g['target_amount']:,.0f} ({pct*100:.0f}%)")
                with c2:
                    new_val = st.number_input("Update ₹", value=float(g['current_amount']), key=f"updg_{g['goal_id']}")
                    if st.button("Save", key=f"btnupd_{g['goal_id']}"):
                        db.update_goal_amount(g['goal_id'], new_val)
                        st.rerun()
                with c3:
                    if st.button("🗑️", key=f"delg_{g['goal_id']}"):
                        db.delete_goal(g['goal_id'])
                        st.rerun()
                st.markdown("---")
        else:
            st.info("No savings goals created yet.")


def show_real_transactions():
    user_id = st.session_state.user['user_id']
    st.markdown('<div class="mode-badge-real">🟢 REAL MODE</div>', unsafe_allow_html=True)
    st.markdown('<p class="main-header">📜 Transaction Log</p>', unsafe_allow_html=True)
    st.markdown("---")

    txns = db.get_transactions(user_id)
    if len(txns) == 0:
        st.info("No transactions logged yet.")
        return

    st.dataframe(
        txns[['transaction_date', 'type', 'category_name', 'title', 'amount', 'wallet_name']]
        .rename(columns={
            'transaction_date': 'Date', 'type': 'Type', 'category_name': 'Category',
            'title': 'Title', 'amount': 'Amount (₹)', 'wallet_name': 'Wallet'
        }),
        use_container_width=True
    )
    
    st.subheader("🗑️ Remove Transaction")
    txn_map = {f"#{r['transaction_id']} | {r['transaction_date']} | {r['category_name']} | ₹{r['amount']:,.0f}": r['transaction_id'] 
               for _, r in txns.head(50).iterrows()}
    chosen = st.selectbox("Select Transaction", list(txn_map.keys()))
    if st.button("Delete Transaction", type="secondary"):
        ok, msg = db.delete_transaction(txn_map[chosen], user_id)
        if ok:
            st.success(msg)
            st.rerun()


# ============================================================
# MAIN ROUTER
# ============================================================
page, selected_months = render_sidebar()

if st.session_state.app_mode == "demo":
    user_id = st.session_state.demo_user_id
    if page == "📊 Analytics Overview":
        show_demo_overview(user_id, selected_months)
    elif page == "📋 Budget Tracker":
        show_demo_budgets(user_id, selected_months)
    elif page == "🔍 Behavior & Anomalies":
        show_demo_behavior(user_id, selected_months)
    elif page == "🎯 Goals & Forecast":
        show_demo_goals_forecast(user_id, selected_months)
    elif page == "📜 Browse Transactions":
        show_demo_transactions(user_id, selected_months)

else:
    # Real Mode
    if not st.session_state.logged_in:
        show_auth_page()
    else:
        if page == "📊 Dashboard":
            show_real_dashboard()
        elif page == "➕ Add Transaction":
            show_real_add_transaction()
        elif page == "💳 Manage Wallets":
            show_real_wallets()
        elif page == "📁 Categories":
            show_real_categories()
        elif page == "📋 Budget Manager":
            show_real_budgets()
        elif page == "🎯 Goals":
            show_real_goals()
        elif page == "📜 All Transactions":
            show_real_transactions()

# Global Footer
st.markdown("---")
st.markdown(
    '<div style="text-align:center; color:#888; font-size: 0.85rem;">'
    '💰 Money Mate Analytics · Dual-Mode (Demo & Live) · '
    '<a href="https://github.com/codeknight2531-bit/money-mate-analytics" target="_blank">GitHub Repository</a>'
    '</div>',
    unsafe_allow_html=True
)

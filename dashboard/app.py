"""
Money Mate: Personal Finance Analytics Dashboard
Live Streamlit app — works with CSV data (no MySQL required for deployment).
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from sklearn.linear_model import LinearRegression
import os
import numpy as np

# --- Page Config ---
st.set_page_config(
    page_title='💰 Money Mate Analytics',
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
    .sub-header {
        font-size: 1.1rem;
        color: #888;
        margin-top: -10px;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea11, #764ba211);
        border-radius: 12px;
        padding: 10px 15px;
        border-left: 4px solid #667eea;
    }
    .stMetric > div { background: transparent; }
</style>
""", unsafe_allow_html=True)

# --- Load Data ---
@st.cache_data
def load_data():
    """Load data from CSV files."""
    base = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(base, '..', 'data')

    tx = pd.read_csv(os.path.join(data_dir, 'transactions.csv'))
    users = pd.read_csv(os.path.join(data_dir, 'users.csv'))
    cats = pd.read_csv(os.path.join(data_dir, 'categories.csv'))
    wallets = pd.read_csv(os.path.join(data_dir, 'wallets.csv'))
    budgets = pd.read_csv(os.path.join(data_dir, 'budgets.csv'))
    goals = pd.read_csv(os.path.join(data_dir, 'goals.csv'))

    tx['transaction_date'] = pd.to_datetime(tx['transaction_date'])
    tx['month'] = tx['transaction_date'].dt.to_period('M').astype(str)
    tx['weekday'] = tx['transaction_date'].dt.day_name()

    budgets['start_date'] = pd.to_datetime(budgets['start_date'])
    budgets['end_date'] = pd.to_datetime(budgets['end_date'])
    budgets['month'] = budgets['start_date'].dt.to_period('M').astype(str)

    return tx, users, cats, wallets, budgets, goals

try:
    tx, users, cats, wallets, budgets, goals = load_data()
except FileNotFoundError:
    st.error("⚠️ Data files not found! Run `python data/generate_data.py` first.")
    st.stop()

# --- Sidebar ---
st.sidebar.markdown("## 🎛️ Filters")
user_names = users.set_index('user_id')['name'].to_dict()
user_options = {f"{v} (ID: {k})": k for k, v in user_names.items()}
selected_user_label = st.sidebar.selectbox('👤 Select User', list(user_options.keys()))
user_id = user_options[selected_user_label]

months_available = sorted(tx[tx.user_id == user_id]['month'].unique())
selected_months = st.sidebar.multiselect(
    '📅 Months', months_available, default=months_available
)

# Filter data
txu = tx[(tx.user_id == user_id) & (tx.month.isin(selected_months))]
bu = budgets[(budgets.user_id == user_id) & (budgets.month.isin(selected_months))]
gu = goals[goals.user_id == user_id]

# --- Header ---
st.markdown('<p class="main-header">💰 Money Mate Analytics</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">Personal Finance Dashboard — Track, Analyze, Optimize</p>', unsafe_allow_html=True)
st.markdown("---")

# ============================================================
# PAGE 1: OVERVIEW
# ============================================================
tab1, tab2, tab3, tab4 = st.tabs([
    "📊 Overview", "💳 Budget Tracker", "🔍 Behavior & Anomalies", "🎯 Goals & Forecast"
])

with tab1:
    # KPI Cards
    income = txu[txu.type == 'income']['amount'].sum()
    expense = txu[txu.type == 'expense']['amount'].sum()
    savings = income - expense
    savings_rate = (savings / income * 100) if income > 0 else 0
    num_txns = len(txu)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("💵 Total Income", f"₹{income:,.0f}")
    c2.metric("💸 Total Expense", f"₹{expense:,.0f}")
    c3.metric("🏦 Net Savings", f"₹{savings:,.0f}",
              delta=f"{savings_rate:.1f}% rate")
    c4.metric("📝 Transactions", f"{num_txns:,}")

    st.markdown("---")

    # Monthly Income vs Expense
    col1, col2 = st.columns([3, 2])

    with col1:
        st.subheader("📈 Monthly Income vs Expense")
        monthly = txu.groupby(['month', 'type'])['amount'].sum().unstack(fill_value=0)
        if 'income' not in monthly.columns:
            monthly['income'] = 0
        if 'expense' not in monthly.columns:
            monthly['expense'] = 0
        monthly = monthly.reset_index()

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
        cat_spend = txu[txu.type == 'expense'].groupby('category_name')['amount'].sum().reset_index()
        cat_spend = cat_spend.sort_values('amount', ascending=False)

        fig2 = px.pie(cat_spend, values='amount', names='category_name',
                      color_discrete_sequence=px.colors.qualitative.Set3,
                      hole=0.4)
        fig2.update_traces(textposition='inside', textinfo='percent+label')
        fig2.update_layout(height=400, showlegend=False)
        st.plotly_chart(fig2, use_container_width=True)

    # Savings Rate Trend
    st.subheader("📉 Monthly Savings Rate Trend")
    if len(monthly) > 0:
        monthly['savings_rate'] = ((monthly['income'] - monthly['expense']) / monthly['income'] * 100).round(1)
        monthly['savings_rate'] = monthly['savings_rate'].fillna(0)

        fig3 = go.Figure()
        fig3.add_trace(go.Scatter(
            x=monthly['month'], y=monthly['savings_rate'],
            mode='lines+markers+text', text=monthly['savings_rate'].astype(str) + '%',
            textposition='top center',
            line=dict(color='#3498db', width=3),
            marker=dict(size=10)
        ))
        fig3.add_hline(y=20, line_dash="dash", line_color="green",
                       annotation_text="20% Target")
        fig3.update_layout(height=350, yaxis_title='Savings Rate (%)',
                           xaxis_title='Month')
        st.plotly_chart(fig3, use_container_width=True)

# ============================================================
# PAGE 2: BUDGET TRACKER
# ============================================================
with tab2:
    st.subheader("📊 Budget vs Actual Spending")

    if len(bu) > 0:
        # Merge budgets with actual spending
        cats_df = cats[cats.user_id == user_id]

        budget_analysis = []
        for _, b in bu.iterrows():
            cat_name = cats_df[cats_df.category_id == b.category_id]['name'].values
            if len(cat_name) == 0:
                continue
            cat_name = cat_name[0]
            actual = txu[
                (txu.category_id == b.category_id) &
                (txu.type == 'expense') &
                (txu.transaction_date >= b.start_date) &
                (txu.transaction_date <= b.end_date)
            ]['amount'].sum()
            budget_analysis.append({
                'month': b.month, 'category': cat_name,
                'budget': b.amount, 'spent': actual,
                'used_pct': round(actual / b.amount * 100, 1) if b.amount > 0 else 0
            })

        ba_df = pd.DataFrame(budget_analysis)

        # Over-budget summary
        over_budget = ba_df[ba_df.used_pct > 100]
        c1, c2, c3 = st.columns(3)
        c1.metric("🔴 Over-Budget Instances", len(over_budget))
        c2.metric("📊 Total Budget Checks", len(ba_df))
        c3.metric("⚡ Worst Overshoot",
                  f"{over_budget.used_pct.max():.0f}%" if len(over_budget) > 0 else "None")

        st.markdown("---")

        # Category-wise budget comparison (latest month)
        latest_month = ba_df['month'].max()
        latest = ba_df[ba_df.month == latest_month]

        fig = go.Figure()
        fig.add_trace(go.Bar(
            y=latest['category'], x=latest['budget'],
            name='Budget', orientation='h', marker_color='#3498db'
        ))
        fig.add_trace(go.Bar(
            y=latest['category'], x=latest['spent'],
            name='Actual', orientation='h', marker_color='#e74c3c'
        ))
        fig.update_layout(
            title=f'Budget vs Actual — {latest_month}',
            barmode='group', height=400, xaxis_title='Amount (₹)'
        )
        st.plotly_chart(fig, use_container_width=True)

        # Over-budget table
        if len(over_budget) > 0:
            st.subheader("🚨 Over-Budget Categories")
            display_cols = ['month', 'category', 'budget', 'spent', 'used_pct']
            st.dataframe(
                over_budget[display_cols].sort_values('used_pct', ascending=False)
                .style.format({'budget': '₹{:,.0f}', 'spent': '₹{:,.0f}', 'used_pct': '{:.1f}%'})
                .background_gradient(subset=['used_pct'], cmap='Reds'),
                use_container_width=True, height=400
            )
    else:
        st.info("No budget data available for selected filters.")

# ============================================================
# PAGE 3: BEHAVIOR & ANOMALIES
# ============================================================
with tab3:
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("💳 Payment Method Split")
        wallet_spend = txu[txu.type == 'expense'].groupby('wallet_name').agg(
            txn_count=('amount', 'count'),
            total_spend=('amount', 'sum')
        ).reset_index()

        fig = px.bar(wallet_spend, x='wallet_name', y='total_spend',
                     color='wallet_name', text='txn_count',
                     color_discrete_sequence=px.colors.qualitative.Pastel,
                     labels={'total_spend': 'Total Spend (₹)', 'wallet_name': 'Payment Method'})
        fig.update_traces(texttemplate='%{text} txns', textposition='outside')
        fig.update_layout(height=400, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("📅 Weekday Spending Pattern")
        day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        weekday_spend = txu[txu.type == 'expense'].groupby('weekday')['amount'].agg(['mean', 'count']).reset_index()
        weekday_spend.columns = ['weekday', 'avg_spend', 'txn_count']
        weekday_spend['weekday'] = pd.Categorical(weekday_spend['weekday'], categories=day_order, ordered=True)
        weekday_spend = weekday_spend.sort_values('weekday')

        fig = px.bar(weekday_spend, x='weekday', y='avg_spend',
                     color='avg_spend', color_continuous_scale='Viridis',
                     labels={'avg_spend': 'Avg Spend (₹)', 'weekday': 'Day'})
        fig.update_layout(height=400, coloraxis_showscale=False)
        st.plotly_chart(fig, use_container_width=True)

    # Month-over-Month change
    st.subheader("📊 Month-over-Month Expense Change")
    mom = txu[txu.type == 'expense'].groupby('month')['amount'].sum().reset_index()
    mom = mom.sort_values('month')
    mom['prev'] = mom['amount'].shift(1)
    mom['change_pct'] = ((mom['amount'] - mom['prev']) / mom['prev'] * 100).round(1)
    mom = mom.dropna()

    fig = go.Figure()
    colors = ['#2ecc71' if x < 0 else '#e74c3c' for x in mom['change_pct']]
    fig.add_trace(go.Bar(
        x=mom['month'], y=mom['change_pct'],
        marker_color=colors, text=mom['change_pct'].astype(str) + '%',
        textposition='outside'
    ))
    fig.update_layout(height=350, yaxis_title='Change (%)', xaxis_title='Month',
                      title='Expense Change vs Previous Month (Green = ↓, Red = ↑)')
    st.plotly_chart(fig, use_container_width=True)

    # Anomaly Detection
    st.subheader("🔍 Anomaly Detection — Unusual Transactions")
    expense_tx = txu[txu.type == 'expense'].copy()
    if len(expense_tx) > 0:
        cat_avg = expense_tx.groupby('category_name')['amount'].mean().reset_index()
        cat_avg.columns = ['category_name', 'avg_amount']
        anomaly_df = expense_tx.merge(cat_avg, on='category_name')
        anomaly_df['ratio'] = (anomaly_df['amount'] / anomaly_df['avg_amount']).round(1)
        anomalies = anomaly_df[anomaly_df['ratio'] > 3].sort_values('amount', ascending=False)

        if len(anomalies) > 0:
            st.warning(f"⚠️ Found **{len(anomalies)}** anomalous transactions (> 3× category average)")
            st.dataframe(
                anomalies[['transaction_date', 'category_name', 'amount', 'avg_amount', 'ratio', 'wallet_name']]
                .rename(columns={
                    'transaction_date': 'Date', 'category_name': 'Category',
                    'amount': 'Amount (₹)', 'avg_amount': 'Avg (₹)',
                    'ratio': 'x Times Avg', 'wallet_name': 'Payment'
                })
                .style.format({'Amount (₹)': '₹{:,.0f}', 'Avg (₹)': '₹{:,.0f}'}),
                use_container_width=True
            )
        else:
            st.success("✅ No anomalous transactions found!")

# ============================================================
# PAGE 4: GOALS & FORECAST
# ============================================================
with tab4:
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("🎯 Goal Progress")
        if len(gu) > 0:
            for _, g in gu.iterrows():
                progress = g.current_amount / g.target_amount
                st.markdown(f"**{g['name']}**")
                st.progress(min(progress, 1.0))
                days_left = (pd.to_datetime(g.target_date) - pd.Timestamp.now()).days
                st.caption(
                    f"₹{g.current_amount:,.0f} / ₹{g.target_amount:,.0f} "
                    f"({progress*100:.1f}%) — {max(days_left, 0)} days left"
                )
                remaining = g.target_amount - g.current_amount
                if days_left > 0:
                    monthly_needed = remaining / (days_left / 30)
                    st.caption(f"💡 Need ₹{monthly_needed:,.0f}/month to reach goal")
                st.markdown("---")
        else:
            st.info("No active goals.")

    with col2:
        st.subheader("🔮 Next Month Expense Forecast")
        monthly_exp = txu[txu.type == 'expense'].groupby('month')['amount'].sum().reset_index()
        monthly_exp = monthly_exp.sort_values('month')

        if len(monthly_exp) >= 3:
            monthly_exp['t'] = range(len(monthly_exp))
            model = LinearRegression()
            model.fit(monthly_exp[['t']], monthly_exp['amount'])
            next_t = len(monthly_exp)
            predicted = model.predict([[next_t]])[0]

            avg_exp = monthly_exp['amount'].mean()
            last_exp = monthly_exp['amount'].iloc[-1]

            st.metric("📊 Predicted Next Month", f"₹{predicted:,.0f}",
                      delta=f"₹{predicted - last_exp:,.0f} vs last month")
            st.metric("📈 12-Month Average", f"₹{avg_exp:,.0f}")

            # Trend chart with forecast
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=monthly_exp['month'], y=monthly_exp['amount'],
                mode='lines+markers', name='Actual',
                line=dict(color='#e74c3c', width=2)
            ))
            # Add forecast point
            fig.add_trace(go.Scatter(
                x=[f"Next"], y=[predicted],
                mode='markers', name='Forecast',
                marker=dict(size=15, color='#f39c12', symbol='star')
            ))
            fig.update_layout(height=350, yaxis_title='Expense (₹)',
                              title='Expense Trend + Forecast')
            st.plotly_chart(fig, use_container_width=True)

            st.caption("⚠️ Simple linear regression baseline. "
                       "For production, consider ARIMA or Prophet.")
        else:
            st.info("Need at least 3 months of data for forecasting.")

    # Top categories per month
    st.subheader("🏆 Top 3 Spending Categories Per Month")
    top_cats = txu[txu.type == 'expense'].groupby(['month', 'category_name'])['amount'].sum().reset_index()
    top_cats['rank'] = top_cats.groupby('month')['amount'].rank(ascending=False, method='min')
    top3 = top_cats[top_cats['rank'] <= 3].sort_values(['month', 'rank'])

    fig = px.bar(top3, x='month', y='amount', color='category_name',
                 barmode='group', color_discrete_sequence=px.colors.qualitative.Set2,
                 labels={'amount': 'Spend (₹)', 'month': 'Month', 'category_name': 'Category'})
    fig.update_layout(height=400, legend_title='Category')
    st.plotly_chart(fig, use_container_width=True)

# --- Footer ---
st.markdown("---")
st.markdown(
    '<div style="text-align:center; color:#888;">'
    '💰 Money Mate Analytics | Built with Streamlit & Plotly | '
    '<a href="https://github.com/Rajsushant25/money-mate-analytics" target="_blank">GitHub</a>'
    '</div>',
    unsafe_allow_html=True
)

# Money Mate Analytics 💰

A **dynamic, multi-user personal finance analytics** web app. Users can sign up, log in, and manage their own finances — add transactions, set budgets, track goals, and view interactive dashboards.

> 🔗 **[Live Demo on Streamlit Cloud](https://codeknight2531-bit-money-mate-analytics-dashboardapp-xxxxxx.streamlit.app)** *(link active after deployment)*

---

## 🌟 Features

### 🔐 Authentication
- User sign-up and login with bcrypt password hashing
- Each user sees only their own data
- Session-based authentication

### 💰 Transaction Management
- Add income and expense transactions
- Choose category, wallet, date, and description
- Delete transactions with automatic wallet balance adjustment
- Filter and search through all transactions

### 💳 Wallet Management
- Create multiple wallets (Bank, UPI, Cash, Credit Card)
- Track real-time balances
- Automatic balance updates on every transaction

### 📁 Categories
- Default categories created on signup
- Add custom income and expense categories
- Delete unused categories

### 📋 Budget Tracking
- Set monthly/weekly budgets per category
- Visual budget vs actual comparison
- Over-budget alerts and color-coded status

### 🎯 Goal Tracking
- Create savings goals with target dates
- Update progress over time
- Monthly savings needed calculator
- Auto-completion when target is reached

### 📊 Analytics Dashboard
- Monthly income vs expense bar charts
- Category-wise spending donut chart
- Payment method analysis
- Savings rate trend with 20% target line
- Anomaly detection (3× category average)
- Next-month expense forecast (Linear Regression)

---

## 🏗️ Architecture

```
money-mate-analytics/
├── dashboard/
│   ├── app.py              → Main Streamlit app (auth + 7 pages)
│   └── database.py         → SQLite database layer (all CRUD ops)
├── schema/                  → MySQL table definitions
├── data/                    → CSV exports + SQLite database
├── sql/                     → Analysis queries + views
├── docs/                    → Insights + screenshots
├── .streamlit/config.toml   → Dark theme
├── requirements.txt         → Python dependencies
└── README.md
```

## 🛠️ Tech Stack

| Layer | Tool |
|-------|------|
| Database | SQLite (portable, no server needed) |
| Auth | bcrypt password hashing |
| Backend | Python + Streamlit |
| Visualization | Plotly (interactive charts) |
| ML | scikit-learn (expense forecast) |
| Deployment | Streamlit Community Cloud (free) |

## 🚀 How to Run

### Quick Start
```bash
git clone https://github.com/codeknight2531-bit/money-mate-analytics.git
cd money-mate-analytics
pip install -r requirements.txt
streamlit run dashboard/app.py
```

That's it! The SQLite database auto-creates on first run. Open `http://localhost:8501`, sign up, and start managing your finances.

### With MySQL (optional)
For MySQL integration, update `.env` with your credentials and run `schema/create_tables.sql`.

## 📸 Dashboard Pages

| Page | Description |
|------|-------------|
| 🔐 Auth | Login / Sign Up |
| 📊 Dashboard | KPIs, charts, budget status, anomalies, forecast |
| ➕ Add Transaction | Quick transaction entry with recent activity |
| 💳 Wallets | Manage payment methods and balances |
| 📁 Categories | Custom income/expense categories |
| 📋 Budget Manager | Set and track budgets |
| 🎯 Goals | Create and update savings goals |
| 📜 Transactions | Filter, search, and delete transactions |

## 💡 Key Insights

1. **Rent + Food = ~58% of expenses** → Meal planning recommended
2. **Oct-Nov shopping 2× higher** → Festival budget needed
3. **UPI = 55% of transactions** → Digital payment dominant
4. **Savings rate: 15-40%** → Freelance income causes variance
5. **8 anomaly transactions** → Automated alerts recommended

## 🔮 Future Work

- Email/SMS budget alerts
- ML-based transaction categorization
- Bank statement CSV import
- Multi-currency support
- Export to PDF reports
- Mobile responsive design

## 📝 Data & Privacy

- Passwords are hashed with bcrypt (never stored in plain text)
- Each user's data is isolated
- SQLite database is portable and self-contained
- No external API calls — everything runs locally

---

Built with ❤️ by [codeknight2531-bit](https://github.com/codeknight2531-bit)

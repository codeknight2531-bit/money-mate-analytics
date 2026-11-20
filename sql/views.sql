-- Money Mate Analytics: Views
USE money_mate;

CREATE OR REPLACE VIEW v_monthly_summary AS
SELECT user_id, DATE_FORMAT(transaction_date, '%Y-%m') AS month,
       SUM(CASE WHEN type = 'income'  THEN amount ELSE 0 END) AS income,
       SUM(CASE WHEN type = 'expense' THEN amount ELSE 0 END) AS expense
FROM transactions GROUP BY user_id, month;

CREATE OR REPLACE VIEW v_category_spend AS
SELECT t.user_id, DATE_FORMAT(t.transaction_date, '%Y-%m') AS month,
       c.name AS category, SUM(t.amount) AS spend
FROM transactions t JOIN categories c ON c.category_id = t.category_id
WHERE t.type = 'expense'
GROUP BY t.user_id, month, c.name;

CREATE OR REPLACE VIEW v_budget_status AS
SELECT b.user_id, DATE_FORMAT(b.start_date, '%Y-%m') AS month, c.name AS category,
       b.amount AS budget, COALESCE(SUM(t.amount), 0) AS spent
FROM budgets b
JOIN categories c ON c.category_id = b.category_id
LEFT JOIN transactions t ON t.category_id = b.category_id AND t.user_id = b.user_id
     AND t.transaction_date BETWEEN b.start_date AND b.end_date
GROUP BY b.budget_id, b.user_id, b.start_date, c.name, b.amount;

CREATE OR REPLACE VIEW v_wallet_usage AS
SELECT t.user_id, w.name AS wallet, COUNT(*) AS txn_count, SUM(t.amount) AS spend
FROM transactions t JOIN wallets w ON w.wallet_id = t.wallet_id
WHERE t.type = 'expense'
GROUP BY t.user_id, w.name;

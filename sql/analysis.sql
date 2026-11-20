-- Money Mate Analytics: Analysis Queries
USE money_mate;

-- Q1. Monthly income vs expense aur savings rate
SELECT DATE_FORMAT(transaction_date, '%Y-%m') AS month,
       SUM(CASE WHEN type = 'income'  THEN amount END) AS income,
       SUM(CASE WHEN type = 'expense' THEN amount END) AS expense,
       ROUND(100 * (SUM(CASE WHEN type = 'income' THEN amount END)
                  - SUM(CASE WHEN type = 'expense' THEN amount END))
                  / SUM(CASE WHEN type = 'income' THEN amount END), 1) AS savings_rate_pct
FROM transactions WHERE user_id = 1
GROUP BY month ORDER BY month;

-- Q2. Category-wise spending share
SELECT c.name AS category, SUM(t.amount) AS spend,
       ROUND(100 * SUM(t.amount) / SUM(SUM(t.amount)) OVER (), 1) AS share_pct
FROM transactions t JOIN categories c ON c.category_id = t.category_id
WHERE t.user_id = 1 AND t.type = 'expense'
GROUP BY c.name ORDER BY spend DESC;

-- Q3. Budget vs actual (over-budget categories)
SELECT DATE_FORMAT(b.start_date, '%Y-%m') AS month, c.name AS category,
       b.amount AS budget, COALESCE(SUM(t.amount), 0) AS spent,
       ROUND(100 * COALESCE(SUM(t.amount), 0) / b.amount, 1) AS used_pct
FROM budgets b
JOIN categories c ON c.category_id = b.category_id
LEFT JOIN transactions t ON t.category_id = b.category_id
     AND t.user_id = b.user_id AND t.transaction_date BETWEEN b.start_date AND b.end_date
WHERE b.user_id = 1
GROUP BY b.budget_id, b.start_date, c.name, b.amount
HAVING used_pct > 100 ORDER BY used_pct DESC;

-- Q4. Month-over-month expense change (LAG)
WITH m AS (
  SELECT DATE_FORMAT(transaction_date, '%Y-%m') AS month, SUM(amount) AS spend
  FROM transactions WHERE user_id = 1 AND type = 'expense' GROUP BY month
)
SELECT month, spend, LAG(spend) OVER (ORDER BY month) AS prev_spend,
       ROUND(100 * (spend - LAG(spend) OVER (ORDER BY month))
                 / LAG(spend) OVER (ORDER BY month), 1) AS mom_change_pct
FROM m;

-- Q5. Top 3 categories per month (RANK)
SELECT * FROM (
  SELECT DATE_FORMAT(t.transaction_date, '%Y-%m') AS month, c.name AS category,
         SUM(t.amount) AS spend,
         RANK() OVER (PARTITION BY DATE_FORMAT(t.transaction_date, '%Y-%m')
                      ORDER BY SUM(t.amount) DESC) AS rnk
  FROM transactions t JOIN categories c ON c.category_id = t.category_id
  WHERE t.user_id = 1 AND t.type = 'expense'
  GROUP BY month, c.name
) x WHERE rnk <= 3;

-- Q6. Wallet / payment method usage
SELECT w.name AS wallet, COUNT(*) AS txn_count, SUM(t.amount) AS spend
FROM transactions t JOIN wallets w ON w.wallet_id = t.wallet_id
WHERE t.user_id = 1 AND t.type = 'expense'
GROUP BY w.name ORDER BY spend DESC;

-- Q7. Anomalies (3x category average)
SELECT t.transaction_id, t.transaction_date, c.name AS category,
       t.amount, ROUND(a.avg_amt) AS category_avg
FROM transactions t
JOIN categories c ON c.category_id = t.category_id
JOIN (SELECT category_id, AVG(amount) AS avg_amt
      FROM transactions WHERE type = 'expense' GROUP BY category_id) a
  ON a.category_id = t.category_id
WHERE t.type = 'expense' AND t.amount > 3 * a.avg_amt
ORDER BY t.amount DESC;

-- Q8. Weekday vs spending
SELECT DAYNAME(transaction_date) AS weekday, ROUND(AVG(amount)) AS avg_spend, COUNT(*) AS txns
FROM transactions WHERE user_id = 1 AND type = 'expense'
GROUP BY weekday, WEEKDAY(transaction_date) ORDER BY WEEKDAY(transaction_date);

-- Q9. Goal progress
SELECT name, target_amount, current_amount,
       ROUND(100 * current_amount / target_amount, 1) AS progress_pct,
       DATEDIFF(target_date, CURDATE()) AS days_left
FROM goals WHERE user_id = 1 AND status = 'active';

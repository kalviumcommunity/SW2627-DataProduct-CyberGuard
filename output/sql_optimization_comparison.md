# SQL Optimization Comparison

## Summary Table
                     Metric       Original      Optimized
           Columns Selected       SELECT *     7 explicit
          Intermediate Rows          40000           5350
Filters Applied Before Join             No            Yes
              Nesting Depth       3 levels 1 level (CTEs)
          Readability Score Hard to follow    Clear steps

## Task 1 - Remove SELECT *
Original query:
```sql
SELECT *
    FROM transactions t
    JOIN customers c ON t.customer_id = c.id
    WHERE strftime('%Y', t.transaction_date) = '2024'
    LIMIT 1000;
```
Optimized query:
```sql
SELECT
        t.transaction_id,      -- business question: which transaction happened?
        t.transaction_date,    -- business question: when did it happen?
        t.amount,              -- business question: how much revenue was recorded?
        t.customer_id,         -- business question: which customer generated it?
        c.customer_name,       -- business question: who is the customer?
        c.country,             -- business question: where is the customer located?
        c.account_type         -- business question: what account tier is this?
    FROM transactions t
    JOIN customers c ON t.customer_id = c.id
    WHERE strftime('%Y', t.transaction_date) = '2024'
    LIMIT 1000;
```
Original columns: 17
Optimized columns: 7
Same core data: True
Original time: 0.0144s
Optimized time: 0.0089s
Original memory: 0.21 MB
Optimized memory: 0.09 MB
Memory reduction: 59.0%
Column reduction: 58.8%

## Task 2 - Filter Before JOIN
Original query:
```sql
SELECT t.transaction_id, t.amount, c.customer_name, p.product_name
    FROM transactions t
    JOIN customers c ON t.customer_id = c.id
    JOIN products p ON t.product_id = p.id
    WHERE t.transaction_date >= '2024-01-01'
      AND t.amount > 100
      AND c.country = 'USA'
    LIMIT 5000;
```
Optimized query:
```sql
WITH filtered_trans AS (
        SELECT transaction_id, customer_id, product_id, transaction_date, amount
        FROM transactions
        WHERE transaction_date >= '2024-01-01'
          AND amount > 100
    )
    SELECT ft.transaction_id, ft.amount, c.customer_name, p.product_name
    FROM filtered_trans ft
    JOIN customers c ON ft.customer_id = c.id
    JOIN products p ON ft.product_id = p.id
    WHERE c.country = 'USA'
    LIMIT 5000;
```
Transactions table size: 40,000
Filtered transactions before join: 5,350
Reduction factor before join: 7.48x
Final row count: 2,265
Results identical: True

## Task 3 - CTEs for Readability
Original query:
```sql
SELECT customer_segment, AVG(revenue_per_transaction) AS avg_transaction_value
    FROM (
        SELECT
            c.customer_segment,
            AVG(t.amount) AS revenue_per_transaction,
            COUNT(DISTINCT t.transaction_id) AS transaction_count
        FROM (
            SELECT t.transaction_id, t.amount, t.customer_id
            FROM transactions t
            WHERE t.transaction_date >= '2024-01-01'
        ) t
        JOIN customers c ON t.customer_id = c.id
        GROUP BY c.customer_segment
    ) grouped
    GROUP BY customer_segment
    ORDER BY avg_transaction_value DESC;
```
Refactored query:
```sql
WITH recent_transactions AS (
        -- Step 1: Filter to recent data.
        SELECT transaction_id, amount, customer_id
        FROM transactions
        WHERE transaction_date >= '2024-01-01'
    ),
    customer_with_segment AS (
        -- Step 2: Join the filtered transactions to customer dimensions.
        SELECT
            rt.transaction_id,
            rt.amount,
            c.customer_segment
        FROM recent_transactions rt
        JOIN customers c ON rt.customer_id = c.id
    ),
    segment_metrics AS (
        -- Step 3: Aggregate to the segment level.
        SELECT
            customer_segment,
            COUNT(DISTINCT transaction_id) AS transaction_count,
            AVG(amount) AS avg_transaction_value,
            SUM(amount) AS total_revenue
        FROM customer_with_segment
        GROUP BY customer_segment
    )
    SELECT
        customer_segment,
        avg_transaction_value
    FROM segment_metrics
    ORDER BY avg_transaction_value DESC;
```
Results identical: True
Original time: 0.0184s
Refactored time: 0.0180s

## Specific Improvements Identified
- Query 1 removed SELECT * so the database returns only the columns the dashboard or report actually needs.
- Query 2 pushes filters into a CTE so the join operates on a smaller working set.
- Query 3 replaces deep nesting with named CTEs so each step can be read and tested independently.

## Best Practices Applied
- Explicit column selection: reduces payload size, memory use, and accidental dependency on unused fields.
- Early filtering: limits intermediate join volume and lowers CPU and I/O cost.
- CTE structuring: improves maintainability and makes the transformation pipeline easier to validate.

## Follow-Up Answers
1. An index on a high-cardinality filter column can speed reads because the engine can locate matching rows without scanning the full table. The tradeoff is extra storage and slower writes, because the index must be maintained on insert, update, and delete.
2. In SQLite, a CTE is primarily a query-planner construct. Depending on how it is used, the planner may inline it or materialize it, so repeated references are not something I would assume blindly. The practical lesson is to use CTEs for clarity first, and verify plans when reuse matters.
3. If the filtered set is still huge, the next tools are partitioning, materialized views, pre-aggregated tables, and carefully chosen indexes. You can also denormalize analytical models or move heavy computation into scheduled ETL instead of doing it at query time.

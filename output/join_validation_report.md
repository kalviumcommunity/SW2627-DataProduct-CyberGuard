# Join Validation Report

Data mode: demo
Customers: 3
Orders: 3

## Task 1: LEFT JOIN with Row Count Validation
Customer groups returned: 3
Raw LEFT JOIN row count: 4
Average orders per customer: 1.00

Why the result grows: this is a one-to-many join. Customers with multiple orders are repeated once per order, and customers without orders remain in the result with NULL order fields.

## Task 2: Unmatched Keys
Customers with no orders: 1
Orphaned orders: 0

## Task 3: Join Type Comparison
INNER rows: 3
LEFT rows: 4
FULL rows: 4

## Task 4: Multi-Table Join
Rows returned: 1
Joined line total: 250.00
Expected line-item total: 250.00

## Task 5: Join Decisions
- LEFT JOIN from customers to orders keeps every customer in the analysis and exposes customers without orders as NULL matches.
- INNER JOIN is for matched-record analysis where missing keys should be excluded.
- FULL OUTER JOIN is for reconciliation because it retains both unmatched customers and unmatched orders.
- Multi-table LEFT JOINs are useful for lineage, but downstream aggregations must be done carefully to avoid double-counting at the line-item level.

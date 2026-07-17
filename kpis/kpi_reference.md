# KPI Reference

## Monthly Active Users (MAU)

- Definition: Distinct customers with at least one transaction in the last 30 days.
- Formula: `COUNT(DISTINCT customer_id) WHERE transaction_date >= TODAY() - 30 days`
- Data Source: `transactions` table (`customer_id`, `transaction_date`)
- Target Range: 5,000 - 6,000
- Owner: Product Manager
- Update Frequency: Daily
- Notes: Indicator of product engagement; seasonal dips in Q4.

## Revenue per Customer

- Definition: Average revenue generated per unique customer in the reporting period.
- Formula: `SUM(amount) / COUNT(DISTINCT customer_id)`
- Data Source: `transactions` table (`customer_id`, `amount`)
- Target Range: $90 - $110
- Owner: Finance Manager
- Update Frequency: Daily
- Notes: Should move with pricing changes and customer mix shifts.

## Churn Rate

- Definition: Share of customers active in the previous period who were inactive in the current period.
- Formula: `COUNT(customers active in period 1 but not period 2) / COUNT(customers active in period 1)`
- Data Source: `transactions` table (`customer_id`, `transaction_date`)
- Target Range: 0% - 5%
- Owner: Customer Success Lead
- Update Frequency: Weekly
- Notes: Higher values usually signal retention issues or product friction.

## Payment Success Rate

- Definition: Percentage of payment attempts that completed successfully.
- Formula: `COUNT(successful payments) / COUNT(all payment attempts)`
- Data Source: `transactions` table (`payment_status`, `transaction_id`)
- Target Range: 95% - 100%
- Owner: Engineering Lead
- Update Frequency: Daily
- Notes: Low values usually point to gateway or fraud-check failures.

## Customer Acquisition Cost (CAC)

- Definition: Average cost to acquire one new customer.
- Formula: `SUM(acquisition_cost) / COUNT(DISTINCT customer_id)`
- Data Source: `marketing_attribution` or `transactions` table (`customer_id`, `acquisition_cost`)
- Target Range: $0 - $50
- Owner: Growth Manager
- Update Frequency: Weekly
- Notes: Watch CAC alongside revenue per customer to keep unit economics healthy.

## Repeat Purchase Rate

- Definition: Percentage of customers who made more than one purchase in the period.
- Formula: `COUNT(customers with >1 transaction) / COUNT(DISTINCT customer_id)`
- Data Source: `transactions` table (`customer_id`, `transaction_date`)
- Target Range: 25% - 45%
- Owner: Product Manager
- Update Frequency: Weekly
- Notes: Useful for understanding loyalty and product stickiness.

## KPI Decomposition Example

### Total Monthly Revenue

- Top-level KPI: `SUM(amount)`
- Segment breakdown: revenue grouped by `customer_type`
- Product breakdown: revenue grouped by `product`

### Revenue per Customer

- Top-level KPI: `SUM(amount) / COUNT(DISTINCT customer_id)`
- Decomposition: `(Revenue from Enterprise + SMB + Startup) / (Enterprise customers + SMB customers + Startup customers)`
- Consistency check: segment revenue should sum to total revenue, and segment customer counts should sum to the unique customer base.

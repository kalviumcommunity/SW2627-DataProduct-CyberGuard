# Dashboard Design Documentation

## Information Hierarchy Applied
- Level 1 (Status): 5 KPI cards at the top provide an immediate answer to "are we on track?" by combining revenue, customer base, efficiency, retention, and satisfaction.
- Level 2 (Trends): 3 time-series charts show whether the business is moving in the right direction and where momentum is changing.
- Level 3 (Segments): 2 comparison charts break performance down by region and customer segment so sales and marketing can see where performance differs.
- Level 4 (Detail): Filters, table, and download option provide drill-down only when users need it.

## KPI Rationale
- Revenue: answers the CEO's core question about business performance.
- Active Customers: shows whether the customer base is expanding or contracting.
- Avg Order Value: reveals whether monetisation is improving.
- Churn Rate: highlights retention risk and customer health.
- NPS Score: gives a quick satisfaction signal that often explains future growth or decline.

## Design Principles Applied
1. Progressive Disclosure: the headline KPIs are visible first, with detail hidden behind filters.
2. Spatial Organisation: the most important metrics are placed in the top row, trends in the middle, and detail at the bottom.
3. Consistent Metaphor: blue is the primary business metric, orange is comparison, green indicates positive movement, and red indicates risk.
4. Context Over Numbers: each metric includes a change indicator, and key charts include target or reference lines.

## Colour Palette
- Primary: #1f77b4 - Revenue and core performance.
- Secondary: #ff7f0e - Comparison series and supporting signals.
- Success: #2ca02c - Positive direction, targets, and healthy outcomes.
- Danger: #d62728 - Risk, churn, and negative movement.

## Target Audience
- CEO: checks the top KPI row to quickly judge whether the business is on track.
- VP of Marketing: uses the campaign trend and campaign ROI views to assess marketing effectiveness.
- Sales Director: uses the revenue-by-region and segment comparison charts to prioritise regions and customer groups.

## Data Sources
- KPI values: derived from monthly revenue, active customer counts, churn, and NPS demo series.
- Trend data: monthly time-series data prepared in the dashboard script.
- Segment data: revenue and conversion comparisons by customer segment and region.
- Detail data: a filtered customer-level table with revenue, last activity, and churn risk.

## Layout Summary
- Top: 5 KPI cards.
- Middle: 3 trend charts.
- Lower middle: 2 segment comparison charts.
- Bottom: interactive filters, data table, and CSV download.
CREATE INDEX IF NOT EXISTS idx_fact_orderdate ON fact_sales(order_date_key);
CREATE INDEX IF NOT EXISTS idx_fact_shipdate  ON fact_sales(ship_date_key);
CREATE INDEX IF NOT EXISTS idx_fact_product   ON fact_sales(product_id);
CREATE INDEX IF NOT EXISTS idx_fact_customer  ON fact_sales(customer_id);
CREATE INDEX IF NOT EXISTS idx_fact_geo       ON fact_sales(geo_key);
CREATE INDEX IF NOT EXISTS idx_fact_shipmode  ON fact_sales(ship_mode);
CREATE INDEX IF NOT EXISTS idx_fact_priority  ON fact_sales(priority);

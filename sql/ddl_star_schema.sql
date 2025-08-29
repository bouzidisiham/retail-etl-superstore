-- Dimensions
CREATE TABLE IF NOT EXISTS dim_date (
  date_key     INTEGER PRIMARY KEY,
  date         DATE NOT NULL,
  year         INTEGER,
  quarter      INTEGER,
  month        INTEGER,
  day          INTEGER,
  week         INTEGER,
  is_weekend   BOOLEAN,
  yyyymm       INTEGER,
  yyyyqq       TEXT
);

CREATE TABLE IF NOT EXISTS dim_customer (
  customer_id   TEXT PRIMARY KEY,
  customer_name TEXT,
  segment       TEXT
);

CREATE TABLE IF NOT EXISTS dim_product (
  product_id    TEXT PRIMARY KEY,
  product_name  TEXT,
  category      TEXT,
  sub_category  TEXT
);

CREATE TABLE IF NOT EXISTS dim_geography (
  geo_key     TEXT PRIMARY KEY,
  country     TEXT,
  state       TEXT,
  city        TEXT,
  region      TEXT,
  market      TEXT,
  market2     TEXT
);

CREATE TABLE IF NOT EXISTS dim_ship (
  ship_mode    TEXT PRIMARY KEY,
  speed_bucket TEXT
);

CREATE TABLE IF NOT EXISTS dim_priority (
  priority      TEXT PRIMARY KEY,
  priority_rank INTEGER
);

-- Faits
CREATE TABLE IF NOT EXISTS fact_sales (
  order_id        TEXT,
  order_line      INTEGER,
  order_date_key  INTEGER REFERENCES dim_date(date_key),
  ship_date_key   INTEGER REFERENCES dim_date(date_key),
  customer_id     TEXT REFERENCES dim_customer(customer_id),
  product_id      TEXT REFERENCES dim_product(product_id),
  geo_key         TEXT REFERENCES dim_geography(geo_key),
  ship_mode       TEXT REFERENCES dim_ship(ship_mode),
  priority        TEXT REFERENCES dim_priority(priority),
  sales           NUMERIC,
  quantity        INTEGER,
  discount        NUMERIC,
  profit          NUMERIC,
  shipping_cost   NUMERIC,
  shipping_days   INTEGER,
  PRIMARY KEY (order_id, order_line)
);

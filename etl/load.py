from sqlalchemy import create_engine, text
from .config import DB_URL
import pandas as pd
import pathlib

def get_engine():
    return create_engine(DB_URL, future=True)

def create_schema(engine, ddl_path="sql/ddl_star_schema.sql"):
    with engine.begin() as conn:
        sql = pathlib.Path(ddl_path).read_text(encoding="utf-8")
        conn.execute(text(sql))

def full_refresh_table(df: pd.DataFrame, table: str, engine):
    with engine.begin() as conn:
        conn.execute(text(f"TRUNCATE TABLE {table} RESTART IDENTITY CASCADE;"))
    df.to_sql(table, engine, if_exists="append", index=False, method="multi", chunksize=1000)

def load_all(dim_customer, dim_product, dim_geography, dim_ship, dim_priority, dim_date, fact_sales):
    eng = get_engine()
    create_schema(eng)
    # dimensions
    full_refresh_table(dim_date, "dim_date", eng)
    full_refresh_table(dim_customer, "dim_customer", eng)
    full_refresh_table(dim_product, "dim_product", eng)
    full_refresh_table(dim_geography, "dim_geography", eng)
    full_refresh_table(dim_ship, "dim_ship", eng)
    if not dim_priority.empty:
        full_refresh_table(dim_priority, "dim_priority", eng)
    # faits
    full_refresh_table(fact_sales, "fact_sales", eng)

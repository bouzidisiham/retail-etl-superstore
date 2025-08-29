import pandas as pd
import numpy as np

def build_dim_date(dates: pd.Series) -> pd.DataFrame:
    s = pd.to_datetime(dates.dropna().unique())
    df = pd.DataFrame({"date": s})
    df["date_key"] = df["date"].dt.strftime("%Y%m%d").astype(int)
    df["year"] = df["date"].dt.year
    df["quarter"] = df["date"].dt.quarter
    df["month"] = df["date"].dt.month
    df["day"] = df["date"].dt.day
    df["week"] = df["date"].dt.isocalendar().week.astype(int)
    df["is_weekend"] = df["date"].dt.dayofweek >= 5
    df["yyyymm"] = (df["year"] * 100 + df["month"]).astype(int)
    df["yyyyqq"] = df["year"].astype(str) + "Q" + df["quarter"].astype(str)
    return df[["date_key","date","year","quarter","month","day","week","is_weekend","yyyymm","yyyyqq"]]

def _bucket_ship(mode: str) -> str:
    m = (mode or "").lower()
    if "same" in m or "first" in m: return "Express"
    if "second" in m: return "Standard+"
    return "Standard"

def _priority_rank(p: str):
    order = {"critical": 1, "high": 2, "medium": 3, "low": 4}
    return order.get((p or "").strip().lower())

def build_dims(df_orders: pd.DataFrame):
    # colonnes possibles manquantes => les créer vides
    for c in ["product_id","product_name","category","sub_category",
              "customer_id","customer_name","segment",
              "country","state","city","region","market","market2",
              "ship_mode","order_priority"]:
        if c not in df_orders.columns:
            df_orders[c] = pd.NA

    # Customer (clé = customer_id)
    dim_customer = (df_orders[["customer_id","customer_name","segment"]]
                    .sort_values(["customer_id","segment","customer_name"])
                    .drop_duplicates(subset=["customer_id"], keep="first")
                    .reset_index(drop=True))

    # Product (clé = product_id)
    dim_product = (df_orders[["product_id","product_name","category","sub_category"]]
                   .sort_values(["product_id","category","sub_category","product_name"])
                   .drop_duplicates(subset=["product_id"], keep="first")
                   .reset_index(drop=True))

    # Geography (clé = geo_key)
    geo = df_orders[["country","state","city","region","market","market2"]].copy()
    for c in geo.columns:
        geo[c] = geo[c].astype(str).str.strip()
    key_parts = [col for col in ["country","state","city","region"] if col in geo.columns]
    geo["geo_key"] = geo[key_parts].fillna("").astype(str).agg("|".join, axis=1)
    dim_geography = (geo[["geo_key","country","state","city","region","market","market2"]]
                     .drop_duplicates(subset=["geo_key"], keep="first")
                     .reset_index(drop=True))

    # Ship (clé = ship_mode)
    dim_ship = df_orders[["ship_mode"]].drop_duplicates().copy()
    dim_ship["speed_bucket"] = dim_ship["ship_mode"].apply(_bucket_ship)

    # Priority (clé = priority)
    dp = df_orders[["order_priority"]].drop_duplicates().copy()
    dp["priority"] = dp["order_priority"]
    dp["priority_rank"] = dp["order_priority"].apply(_priority_rank)
    dim_priority = dp[["priority","priority_rank"]].drop_duplicates(subset=["priority"]).reset_index(drop=True)

    # Dates (commande + expédition) — unique par date_key
    dim_date = pd.concat([
        build_dim_date(df_orders["order_date"]),
        build_dim_date(df_orders["ship_date"])
    ]).drop_duplicates(subset=["date_key"]).reset_index(drop=True)

    return dim_customer, dim_product, dim_geography, dim_ship, dim_priority, dim_date

def build_fact(df_orders: pd.DataFrame) -> pd.DataFrame:
    df = df_orders.copy()

    # sécurité colonnes manquantes
    for c in ["order_id","order_date","ship_date","customer_id","product_id","ship_mode",
              "sales","quantity","discount","profit","shipping_cost",
              "country","state","city","region"]:
        if c not in df.columns:
            df[c] = pd.NA

    # dérivés
    df["order_line"] = df.groupby("order_id").cumcount() + 1
    df["order_date_key"] = pd.to_datetime(df["order_date"]).dt.strftime("%Y%m%d").astype("Int64")
    df["ship_date_key"]  = pd.to_datetime(df["ship_date"]).dt.strftime("%Y%m%d").astype("Int64")
    df["shipping_days"]  = (pd.to_datetime(df["ship_date"]) - pd.to_datetime(df["order_date"])).dt.days

    df["geo_key"] = (df["country"].fillna("") + "|" + df["state"].fillna("") + "|" +
                     df["city"].fillna("") + "|" + df["region"].fillna(""))

    cols = ["order_id","order_line","order_date_key","ship_date_key","customer_id","product_id",
            "geo_key","ship_mode","sales","quantity","discount","profit","shipping_cost","shipping_days"]
    if "order_priority" in df.columns:
        cols.append("order_priority")
    fact = df[cols].rename(columns={"order_priority":"priority"})
    return fact

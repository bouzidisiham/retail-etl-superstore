import  re
import pandas as pd
from .config import DATA_PATH,  ENCODING, DECIMAL, SEP

def read_orders() -> pd.DataFrame:
    sep_arg = None if (str(SEP).lower() == "auto") else SEP
    df = pd.read_csv(DATA_PATH, sep=sep_arg, engine="python", encoding=ENCODING, decimal=DECIMAL)

    # normalisation colonnes : tout sauf [a-z0-9] => "_"
    df.columns = [re.sub(r"[^0-9a-zA-Z]+", "_", c).strip("_").lower() for c in df.columns]

    # cast dates
    for c in ["order_date","ship_date"]:
        if c in df.columns:
            df[c] = pd.to_datetime(df[c], errors="coerce")

    # cast numériques
    for c in ["sales","profit","discount","quantity","shipping_cost"]:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")

    # strings utiles
    for c in ["product_id","customer_id","country","state","city","region","market","market2",
              "product_name","category","sub_category","ship_mode","order_priority"]:
        if c in df.columns:
            df[c] = df[c].astype(str).str.strip()

    # postal code => texte si présent
    if "postal_code" in df.columns:
        df["postal_code"] = df["postal_code"].astype(str).str.strip()

    # discount en %
    if "discount" in df.columns and df["discount"].dropna().max() > 1:
        df["discount"] = df["discount"] / 100.0

    return df

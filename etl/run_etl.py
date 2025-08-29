from etl.extract import read_orders
from etl.transform import build_dims, build_fact
from etl.load import load_all

def main():
    orders = read_orders()

    # Contrôles qualité clés
    assert not orders["order_id"].isna().any(), "order_id manquant"
    for c in ["sales","profit","quantity"]:
        assert c in orders.columns and orders[c].notna().all(), f"valeurs manquantes dans {c}"
    if "ship_date" in orders.columns and "order_date" in orders.columns:
        bad_dates = (orders["ship_date"] < orders["order_date"]).sum()
        if bad_dates > 0:
            print(f"⚠️ {bad_dates} lignes avec ship_date < order_date")

    dim_customer, dim_product, dim_geography, dim_ship, dim_priority, dim_date = build_dims(orders)
    fact_sales = build_fact(orders)

    load_all(dim_customer, dim_product, dim_geography, dim_ship, dim_priority, dim_date, fact_sales)
    print("ETL terminé ✅")

if __name__ == "__main__":
    main()

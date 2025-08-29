import os
import pandas as pd
from sqlalchemy import create_engine
from dash import Dash, html, dcc, Input, Output
import plotly.express as px

# -------------------- Connexion DB --------------------
DB_URL = os.getenv("DB_URL", "postgresql+psycopg2://postgres:postgres@localhost:5432/superstore")
engine = create_engine(DB_URL, future=True)

def load_df():
    # On exploite toutes les dimensions utiles : date, client/segment, produit (cat, subcat),
    # géographie (country/state/city/region/market/market2), ship (speed_bucket), priority (rank)
    q = """
    SELECT
        f.order_id, f.order_line, f.order_date_key, f.ship_date_key,
        f.customer_id, f.product_id, f.geo_key, f.ship_mode, f.priority,
        f.sales, f.quantity, f.discount, f.profit, f.shipping_cost, f.shipping_days,
        d.date AS order_date,
        c.customer_name, c.segment,
        p.category, p.sub_category, p.product_name,
        g.country, g.state, g.city, g.region, g.market, g.market2,
        s.speed_bucket,
        pr.priority_rank
    FROM fact_sales f
    JOIN dim_date      d  ON d.date_key    = f.order_date_key
    JOIN dim_customer  c  ON c.customer_id = f.customer_id
    JOIN dim_product   p  ON p.product_id  = f.product_id
    JOIN dim_geography g  ON g.geo_key     = f.geo_key
    LEFT JOIN dim_ship s   ON s.ship_mode  = f.ship_mode
    LEFT JOIN dim_priority pr ON pr.priority = f.priority
    """
    df = pd.read_sql(q, engine)
    # Typage sécurisé
    df["order_date"] = pd.to_datetime(df["order_date"], errors="coerce")
    for col in ["sales","profit","discount","quantity","shipping_cost","shipping_days"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    # Nettoyage léger
    for col in ["market","market2","region","segment","category","sub_category","ship_mode","priority","speed_bucket"]:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip()
    return df

df = load_df()
date_min = pd.to_datetime(df["order_date"].min())
date_max = pd.to_datetime(df["order_date"].max())

# -------------------- App Dash --------------------
app = Dash(__name__)
app.title = "Global Superstore — Analytics"

# ---- Filtres (multi-dims + période + Top N) ----
filters_row = html.Div([
    dcc.Dropdown(sorted(df["market"].dropna().unique()), multi=True, placeholder="Market", id="f_market"),
    dcc.Dropdown(sorted(df["region"].dropna().unique()), multi=True, placeholder="Region", id="f_region"),
    dcc.Dropdown(sorted(df["segment"].dropna().unique()), multi=True, placeholder="Segment", id="f_segment"),
    dcc.Dropdown(sorted(df["category"].dropna().unique()), multi=True, placeholder="Category", id="f_category"),
    dcc.Dropdown(sorted(df["ship_mode"].dropna().unique()), multi=True, placeholder="Ship Mode", id="f_ship"),
    dcc.Dropdown(sorted(df["priority"].dropna().unique()), multi=True, placeholder="Priority", id="f_priority"),
    dcc.DatePickerRange(
        id="f_dates",
        min_date_allowed=date_min,
        max_date_allowed=date_max,
        start_date=date_min,
        end_date=date_max,
        display_format="YYYY-MM-DD"
    ),
    html.Div([
        html.Label("Top N sous-catégories"),
        dcc.Slider(id="f_topn", min=5, max=20, step=1, value=12,
                   marks={i: str(i) for i in [5,8,10,12,15,20]})
    ], style={"padding":"0 8px"})
], style={
    "display":"grid",
    "gridTemplateColumns":"repeat(7, 1fr) 1.2fr",
    "gap":"10px",
    "margin":"8px 0"
})

# ---- KPI ----
kpi_card = {"border":"1px solid #eee","borderRadius":"12px","padding":"12px",
            "boxShadow":"0 1px 4px rgba(0,0,0,0.05)","background":"#fff"}
kpis = html.Div([
    html.Div([html.Div("Ventes (période)"), html.H2(id="kpi_sales")], style=kpi_card),
    html.Div([html.Div("Profit (période)"), html.H2(id="kpi_profit")], style=kpi_card),
    html.Div([html.Div("Marge % (période)"), html.H2(id="kpi_margin")], style=kpi_card),
    html.Div([html.Div("Livraison (jours moy.)"), html.H2(id="kpi_shipdays")], style=kpi_card),
], style={"display":"grid","gridTemplateColumns":"repeat(4, 1fr)","gap":"12px","margin":"12px 0"})

# ---- 8 Graphes (3 par ligne) ----
graphs_grid = html.Div([
    dcc.Graph(id="g_sales_month"),        # 1. Ventes mensuelles
    dcc.Graph(id="g_profit_month"),       # 2. Profit mensuel
    dcc.Graph(id="g_sales_category"),     # 3. Ventes par catégorie
    dcc.Graph(id="g_margin_category"),    # 4. Marge % par catégorie
    dcc.Graph(id="g_top_subcat"),         # 5. Top N sous-catégories
    dcc.Graph(id="g_profit_region"),      # 6. Profit par région
    dcc.Graph(id="g_sales_ship_speed"),   # 7. Ventes par vitesse d’expédition
    dcc.Graph(id="g_discount_profit"),    # 8. Remise vs Profit
], style={"display":"grid","gridTemplateColumns":"repeat(3, 1fr)","gap":"16px"})

app.layout = html.Div([
    html.H1("Global Superstore — Performance"),
    filters_row,
    kpis,
    graphs_grid
], style={"maxWidth":"1500px","margin":"0 auto","padding":"24px","background":"#f7f7fb"})

# -------------------- Helpers --------------------
def fmt_money(x): 
    try: return f"{x:,.0f}".replace(",", " ")
    except Exception: return "0"

def fmt_pct(x):
    import math
    return f"{x:.1f}%" if x is not None and not math.isnan(x) else "—"

def fmt_days(x):
    import math
    return f"{x:.1f} j" if x is not None and not math.isnan(x) else "—"

def safe_pct(num, den):
    return (num / den * 100.0) if den and den != 0 else None

def apply_filters(base: pd.DataFrame, market, region, segment, category, ship, priority, start_date, end_date):
    dff = base.copy()
    if market:   dff = dff[dff["market"].isin(market)]
    if region:   dff = dff[dff["region"].isin(region)]
    if segment:  dff = dff[dff["segment"].isin(segment)]
    if category: dff = dff[dff["category"].isin(category)]
    if ship:     dff = dff[dff["ship_mode"].isin(ship)]
    if priority: dff = dff[dff["priority"].isin(priority)]

    if start_date: start = pd.to_datetime(start_date)
    else:          start = dff["order_date"].min()
    if end_date:   end   = pd.to_datetime(end_date)
    else:          end   = dff["order_date"].max()

    return dff[(dff["order_date"] >= start) & (dff["order_date"] <= end)]

def empty_fig(title):
    fig = px.scatter(pd.DataFrame({"x":[], "y":[]}), x="x", y="y", title=title)
    fig.update_layout(margin=dict(l=20,r=20,t=50,b=20), height=360)
    return fig

# -------------------- Callback --------------------
@app.callback(
    # KPIs
    Output("kpi_sales","children"),
    Output("kpi_profit","children"),
    Output("kpi_margin","children"),
    Output("kpi_shipdays","children"),
    # Figures
    Output("g_sales_month","figure"),
    Output("g_profit_month","figure"),
    Output("g_sales_category","figure"),
    Output("g_margin_category","figure"),
    Output("g_top_subcat","figure"),
    Output("g_profit_region","figure"),
    Output("g_sales_ship_speed","figure"),
    Output("g_discount_profit","figure"),
    # Filtres
    Input("f_market","value"),
    Input("f_region","value"),
    Input("f_segment","value"),
    Input("f_category","value"),
    Input("f_ship","value"),
    Input("f_priority","value"),
    Input("f_dates","start_date"),
    Input("f_dates","end_date"),
    Input("f_topn","value"),
)
def update(market, region, segment, category, ship, priority, start_date, end_date, topn):
    dff = apply_filters(df, market, region, segment, category, ship, priority, start_date, end_date)

    # ----- KPIs -----
    sales = float(dff["sales"].sum()) if "sales" in dff else 0.0
    profit = float(dff["profit"].sum()) if "profit" in dff else 0.0
    margin = safe_pct(profit, sales)
    shipdays = float(dff["shipping_days"].mean()) if "shipping_days" in dff and len(dff) else None

    k_sales = fmt_money(sales)
    k_profit = fmt_money(profit)
    k_margin = fmt_pct(margin if margin is not None else 0.0)
    k_shipdays = fmt_days(shipdays) if shipdays is not None else "—"

    # Si dataset vide après filtres → figures vides
    if dff.empty:
        return (k_sales, k_profit, k_margin, k_shipdays,
                empty_fig("Ventes mensuelles"),
                empty_fig("Profit mensuel"),
                empty_fig("Ventes par catégorie"),
                empty_fig("Marge % par catégorie"),
                empty_fig("Top sous-catégories"),
                empty_fig("Profit par région"),
                empty_fig("Ventes par vitesse d’expédition"),
                empty_fig("Remise vs Profit"))

    # Agrégations utiles
    dff["yyyymm"] = pd.to_datetime(dff["order_date"], errors="coerce").dt.to_period("M").astype(str)

    # 1) Ventes mensuelles
    by_month_sales = dff.groupby("yyyymm", as_index=False)["sales"].sum().sort_values("yyyymm")
    fig_sales_month = px.line(by_month_sales, x="yyyymm", y="sales", title="Ventes mensuelles")
    fig_sales_month.update_layout(margin=dict(l=20,r=20,t=50,b=20), height=360)

    # 2) Profit mensuel
    by_month_profit = dff.groupby("yyyymm", as_index=False)["profit"].sum().sort_values("yyyymm")
    fig_profit_month = px.line(by_month_profit, x="yyyymm", y="profit", title="Profit mensuel")
    fig_profit_month.update_layout(margin=dict(l=20,r=20,t=50,b=20), height=360)

    # 3) Ventes par catégorie
    by_cat = dff.groupby("category", as_index=False)[["sales","profit"]].sum()
    by_cat["margin_pct"] = by_cat.apply(lambda r: safe_pct(r["profit"], r["sales"]), axis=1)
    by_cat = by_cat.sort_values("sales", ascending=False)
    fig_sales_cat = px.bar(by_cat, x="category", y="sales", hover_data=["profit","margin_pct"],
                           title="Ventes par catégorie")
    fig_sales_cat.update_layout(margin=dict(l=20,r=20,t=50,b=20), height=360)

    # 4) Marge % par catégorie
    fig_margin_cat = px.bar(by_cat.sort_values("margin_pct", ascending=False),
                            x="category", y="margin_pct", title="Marge % par catégorie")
    fig_margin_cat.update_layout(margin=dict(l=20,r=20,t=50,b=20), height=360)

    # 5) Top N sous-catégories (configurable)
    topn = int(topn) if topn else 12
    by_sub = (dff.groupby("sub_category", as_index=False)[["sales","profit"]]
                .sum().sort_values("sales", ascending=False).head(topn))
    fig_top_sub = px.bar(by_sub, x="sub_category", y="sales", hover_data=["profit"],
                         title=f"Top {topn} — Ventes par sous-catégorie")
    fig_top_sub.update_layout(margin=dict(l=20,r=20,t=50,b=20), height=360)

    # 6) Profit par région (horizontal)
    by_reg = dff.groupby("region", as_index=False)["profit"].sum().sort_values("profit", ascending=True)
    fig_profit_region = px.bar(by_reg, y="region", x="profit", orientation="h", title="Profit par région")
    fig_profit_region.update_layout(margin=dict(l=20,r=20,t=50,b=20), height=360)

    # 7) Ventes par vitesse d’expédition (dérivée de ship_mode via dim_ship)
    #    Regroupement plus lisible que par ship_mode brut.
    if "speed_bucket" in dff.columns and dff["speed_bucket"].notna().any():
        by_speed = dff.groupby("speed_bucket", as_index=False)["sales"].sum().sort_values("sales", ascending=False)
        fig_ship_speed = px.bar(by_speed, x="speed_bucket", y="sales", title="Ventes par vitesse d’expédition")
    else:
        by_ship = dff.groupby("ship_mode", as_index=False)["sales"].sum().sort_values("sales", ascending=False)
        fig_ship_speed = px.bar(by_ship, x="ship_mode", y="sales", title="Ventes par mode d’expédition")
    fig_ship_speed.update_layout(margin=dict(l=20,r=20,t=50,b=20), height=360)

    # 8) Remise vs Profit (bulles) — insight sur l'impact des discounts
    fig_disc_profit = px.scatter(
        dff, x="discount", y="profit", size="sales",
        hover_data=["product_name","category","sub_category","customer_name","segment","priority"],
        title="Remise vs Profit (taille = ventes)"
    )
    fig_disc_profit.update_layout(margin=dict(l=20,r=20,t=50,b=20), height=360)

    return (
        k_sales, k_profit, k_margin, k_shipdays,
        fig_sales_month, fig_profit_month, fig_sales_cat, fig_margin_cat,
        fig_top_sub, fig_profit_region, fig_ship_speed, fig_disc_profit
    )

if __name__ == "__main__":
    app.run(debug=True)

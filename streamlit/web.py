import streamlit as st
import pandas as pd
import numpy as np

import plotly.express as px
import plotly.graph_objects as go

from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error

# -------------------------
# Custom CSS (Modern UI)
# -------------------------
st.markdown("""
<style>
body {
    background-color: #0e1117;
    color: white;
}
.metric-card {
    background: #1c1f26;
    padding: 20px;
    border-radius: 12px;
    text-align: center;
}
.section {
    background: #161a23;
    padding: 20px;
    border-radius: 12px;
    margin-bottom: 20px;
}
</style>
""", unsafe_allow_html=True)

st.title("Data-Driven Demand Supply Optimization Dashboard")

# -------------------------
# Upload CSV
# -------------------------
uploaded_file = st.file_uploader("Upload Dataset", type=["csv"])

if uploaded_file is not None:

    df = pd.read_csv(uploaded_file)

    # -------------------------
    # Preprocessing
    # -------------------------
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values(by="date")

    df["day_of_week"] = df["date"].dt.dayofweek
    df["month"] = df["date"].dt.month
    df["year"] = df["date"].dt.year



# -------------------------
# EDA
# -------------------------

# Demand Over Time
    st.subheader("Demand Over Time")

    fig = px.line(
    df,
    x="date",
    y="demand",
    title="Demand Over Time"
    )

    st.plotly_chart(fig, use_container_width=True)


# Demand by Day of Week
    st.subheader("Demand by Week")

    day_df = df.groupby("day_of_week", as_index=False)["demand"].mean()

    fig = px.bar(
    day_df,
    x="day_of_week",
    y="demand",
    title="Average Demand by Day",
    color="demand",
    color_continuous_scale="Blues"
    )

    st.plotly_chart(fig, use_container_width=True)


# Promotional Impact
    st.subheader("Promotional Impact")

    promo_df = df.groupby("promotion", as_index=False)["demand"].mean()

    promo_df["promotion"] = promo_df["promotion"].map({
    0: "Without Promotion",
    1: "With Promotion"
    })

    fig = px.bar(
    promo_df,
    x="promotion",
    y="demand",
    title="Impact of Promotion on Demand",
    color="demand",
    color_continuous_scale="Viridis"
    )

    st.plotly_chart(fig, use_container_width=True)


# -------------------------
# Product Selection
# -------------------------
    products = df["product_id"].unique()

    selected_products = st.multiselect(
        "Select up to 3 products",
        products,
        default=list(products[:1])
    )

    if len(selected_products) == 0:
        st.warning("Select at least one product")
        st.stop()

    df_selected = df[df["product_id"].isin(selected_products)]
    selected_product = selected_products[0]
    df_product = df[df["product_id"] == selected_product]

# -------------------------
# KPI Section
# -------------------------
    col1, col2, col3 = st.columns(3)

    total_demand = int(df_product["demand"].sum())
    avg_demand = int(df_product["demand"].mean())
    max_demand = int(df_product["demand"].max())

    col1.metric("Total Demand", total_demand)
    col2.metric("Average Demand", avg_demand)
    col3.metric("Peak Demand", max_demand)


# -------------------------
# Product Comparison Chart
# -------------------------
    st.markdown("### Product Comparison")

    fig = go.Figure()

    for product in selected_products:
        temp = df[df["product_id"] == product]
        temp = temp.groupby("date", as_index=False)["demand"].sum()

    fig.add_trace(go.Scatter(
        x=temp["date"],
        y=temp["demand"],
        mode="lines",
        name=str(product)
    ))

    fig.update_layout(
    title="Demand Comparison Across Products",
    xaxis_title="Date",
    yaxis_title="Demand",
    template="plotly_dark",
    hovermode="x unified"
    )

    st.plotly_chart(fig, use_container_width=True)


# -------------------------
# Demand Trend (Full Width)
# -------------------------
    st.markdown("### Daily Demand Trend")

    fig1 = px.line(
    df_product,
    x="date",
    y="demand",
    title="Daily Demand Trend"
    )

    fig1.update_traces(line=dict(color="#00d4ff", width=3))

    fig1.update_layout(
    xaxis_title="Date",
    yaxis_title="Demand (Units)",
    template="plotly_dark",
    title_x=0.5
    )

    st.plotly_chart(fig1, use_container_width=True)


# -------------------------
# Product Life Cycle (Full Width)
# -------------------------
    st.markdown("### Product Life Cycle Stages")

    fig2 = go.Figure()

    fig2.add_trace(go.Scatter(
    x=df_product["date"],
    y=df_product["demand"],
    mode="lines",
    name="Demand",
    line=dict(color="#2ecc71", width=3),
    fill="tozeroy"   # gives a nice area effect
    ))

    fig2.update_layout(
    title="Product Life Cycle Curve",
    xaxis_title="Date",
    yaxis_title="Demand",
    template="plotly_dark",
    title_x=0.5,
    hovermode="x unified"
    )

    st.plotly_chart(fig2, use_container_width=True)

    
    for idx, product in enumerate(selected_products):
        df_p = df[df["product_id"] == product].copy()
        lifecycle_df = df_p.groupby("date")["demand"].sum().reset_index()
        lifecycle_df = lifecycle_df.sort_values("date").reset_index(drop=True)

        n = len(lifecycle_df)
    
        if n < 10:
            st.warning(f"Not enough data for {product} lifecycle.")
            continue

    # 5-stage split
        s1 = int(n * 0.15)
        s2 = int(n * 0.25)
        s3 = int(n * 0.25)
        s4 = int(n * 0.20)
        s5 = n - (s1 + s2 + s3 + s4)

        trend_values = np.concatenate([
            np.linspace(10, 30, s1),   # Dev
            np.linspace(30, 80, s2),   # Intro
            np.linspace(80, 150, s3),  # Growth
            np.linspace(150, 140, s4), # Maturity
            np.linspace(140, 60, s5)   # Decline
        ])
    
        lifecycle_df["trend"] = trend_values[:n]


    fig2 = go.Figure()

# Trend line
    fig2.add_trace(go.Scatter(
    x=lifecycle_df["date"],
    y=lifecycle_df["trend"],
    mode="lines",
    name=f"Trend: {product}",
    line=dict(color="#2ecc71", width=4),
    ))

# Stage setup
    boundaries = [0, s1, s1+s2, s1+s2+s3, s1+s2+s3+s4, n-1]
    stage_names = ["Development", "Introduction", "Growth", "Maturity", "Decline"]
    zone_colors = ["#2d82c4", "#2f3640", "#1e272e", "#2f3640", "#1e272e"]

# Add zones + lines + labels
    for i in range(len(stage_names)):
        start_date = lifecycle_df.iloc[boundaries[i]]["date"]
        end_date = lifecycle_df.iloc[boundaries[i+1]]["date"]

    # Background shaded region
    fig2.add_vrect(
        x0=start_date,
        x1=end_date,
        fillcolor=zone_colors[i],
        opacity=0.3,
        layer="below",
        line_width=0,
    )

    # Vertical boundary line
    fig2.add_vline(
        x=end_date,
        line=dict(color="white", dash="dash", width=1),
        opacity=0.4
    )

    # Stage label
    mid_idx = (boundaries[i] + boundaries[i+1]) // 2
    mid_date = lifecycle_df.iloc[mid_idx]["date"]

    fig2.add_annotation(
        x=mid_date,
        y=lifecycle_df["trend"].max(),  # dynamic instead of hardcoded 160
        text=stage_names[i],
        showarrow=False,
        font=dict(color="white", size=12),
        xanchor="center",
        yanchor="bottom"
    )

# Layout styling
    fig2.update_layout(
    title="Product Life Cycle Stages",
    xaxis_title="Date",
    yaxis_title="Trend",
    template="plotly_dark",
    title_x=0.5,
    hovermode="x unified"
    )

    st.plotly_chart(fig2, use_container_width=True)


    fig2.update_layout(
    # Background colors
    plot_bgcolor="#0e1117",
    paper_bgcolor="#0e1117",

    # Axis labels
    xaxis_title="Timeline",
    yaxis_title="Demand Level",

    # Axis styling
    xaxis=dict(
        showgrid=False,
        color="white"
    ),
    yaxis=dict(
        range=[0, 180],
        showgrid=True,
        gridcolor="rgba(255,255,255,0.1)",
        color="white"
    ),

    # Legend
    legend=dict(
        x=0,
        y=1,
        bgcolor="rgba(0,0,0,0)"
    ),

    # Title alignment (if you have one)
    title_x=0.5
    )

    st.plotly_chart(fig2, use_container_width=True)

    # -------------------------
    # ML Model
    # -------------------------
    features = [
        "inventory", "lead_time", "price",
        "discount", "promotion", "day_of_week", "month"
    ]

    
    X = df_product[features]
    y = df_product["demand"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    model = RandomForestRegressor(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)

    preds = model.predict(X_test)

    mae = mean_absolute_error(y_test, preds)

    # -------------------------
    # Model Performance Cards
    # -------------------------
    st.markdown("### Model Insights")

    col1, col2 = st.columns(2)
    col1.metric("Mean Absolute Error", round(mae, 2))
    col2.metric("Demand Standard Deviation", round(np.std(y_train), 2))


    st.subheader("Actual vs Predicted Demand")

    fig = go.Figure()

# Actual values
    fig.add_trace(go.Scatter(
    y=y_test.values,
    mode="lines",
    name="Actual Demand (Units)",
    line=dict(color="#00d4ff", width=3)
    ))

# Predicted values
    fig.add_trace(go.Scatter(
    y=preds,
    mode="lines",
    name="Predicted Demand (Units)",
    line=dict(color="#ff6b6b", width=3)
    ))

    fig.update_layout(
    title="Model Prediction vs Actual",
    xaxis_title="Sample Index",
    yaxis_title="Demand (Units)",
    template="plotly_dark",
    hovermode="x unified",
    title_x=0.5
    )

    st.plotly_chart(fig, use_container_width=True)

    # -------------------------
    # Scenario Simulation
    # -------------------------
    st.markdown("### Scenario Simulation (What-if Analysis)")

    # User input
    demand_scenario = st.slider(
    "Demand Change (%)",
    min_value=-50,
    max_value=100,
    value=0
    )

    scenario_factor = 1 + (demand_scenario / 100)

    # Adjust predictions
    scenario_demand = preds * scenario_factor

    # Recompute order
    scenario_order = scenario_demand * 1.10  # buffer included

    fig = go.Figure()

    fig.add_trace(go.Scatter(
    y=preds,
    mode="lines",
    name="Base Prediction",
    line=dict(color="#00d4ff", width=3)
    ))

    fig.add_trace(go.Scatter(
    y=scenario_demand,
    mode="lines",
    name="Scenario Demand",
    line=dict(color="#ffcc00", width=3) 
    ))

    fig.add_trace(go.Scatter(
    y=scenario_order,
    mode="lines",
    name="Scenario Order Plan",
    line=dict(color="#2ecc71", width=3)
    ))

    fig.update_layout(
    title="Scenario Simulation: Demand vs Inventory Plan",
    xaxis_title="Sample Index",
    yaxis_title="Units",
    template="plotly_dark",
    hovermode="x unified",
    title_x=0.5
    )

    st.plotly_chart(fig, use_container_width=True)

    # -------------------------
    # Agent Output Table
    # -------------------------
    st.markdown("### Recommendations for next quater")
    st.dataframe(X_test.head(), use_container_width=True)

    # -------------------------
    # Replenishment Decision
    # -------------------------
    st.markdown("### Inventory Replenishment Decision")

    # Safety buffer (can also be user-controlled later)
    buffer_pct = 0.10  # 10% buffer

    recommended_order = preds * (1 + buffer_pct)

    decision_df = pd.DataFrame({
    "Predicted Demand": preds,
    "Recommended Order": recommended_order
    })

    st.dataframe(decision_df, use_container_width=True)



    # -------------------------
    # Recommendation Chart
    # -------------------------

    st.markdown("### Inventory Decisions")

    fig = go.Figure()

# Predicted Demand
    fig.add_trace(go.Scatter(
    y=preds,
    mode="lines",
    name="Predicted Demand (Units)",
    line=dict(color="#00d4ff", width=3)
    ))

# Recommended Order
    recommended_order=preds*1.1
    fig.add_trace(go.Scatter(
    y=recommended_order,
    mode="lines",
    name="Recommended Order (Units)",
    line=dict(color="#2ecc71", width=3)
    ))

    fig.update_layout(
    title="Inventory Decision vs Demand",
    xaxis_title="Sample Index",
    yaxis_title="Units",
    template="plotly_dark",
    hovermode="x unified",
    title_x=0.5
    )

    st.plotly_chart(fig, use_container_width=True)


    # -------------------------
    # 📊 Safety Stock Logic
    # -------------------------
    st.markdown("### 📊 Safety Stock Recommendation")

    demand_std = np.std(y_train)
    service_level_factor = 1.65  # ~95% service level (z-score)

    safety_stock = service_level_factor * demand_std

    st.metric("Demand Standard Deviation", round(demand_std, 2))
    st.metric("Safety Stock (Units)", round(safety_stock, 2))

    adjusted_order = preds + safety_stock

    st.write("Adjusted Order with Safety Stock:")
    st.dataframe(
    pd.DataFrame({
        "Predicted Demand": preds,
        "Safety Stock": safety_stock,
        "Final Order": adjusted_order
    }),
    use_container_width=True
    )
    
    # -------------------------
    # Cost Analysis
    # -------------------------
    holding_cost = 2
    stockout_cost = 5

    costs = []

    for i in range(len(X_test)):
        demand = y_test.values[i]
        inventory = X_test.iloc[i]["inventory"]

        if inventory > demand:
            cost = (inventory - demand) * holding_cost
        else:
            cost = (demand - inventory) * stockout_cost

        costs.append(cost)

    st.markdown("### 💰 Cost Analysis for next quater (in Rupees)")
    st.metric("Estimated Average Cost for in Rupees ₹", round(np.mean(costs), 2))


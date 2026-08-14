import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Customer Analysis", page_icon="👥", layout="wide")

@st.cache_data
def load_data():
    return pd.read_csv("data/customer_purchases.csv", parse_dates=["Order_Date"])

df = load_data()

st.title("👥 Customer Analysis Dashboard")
st.caption("Analyze customer purchases and identify the most valuable customers.")

st.sidebar.header("Filters")
categories = st.sidebar.multiselect(
    "Category", sorted(df["Category"].unique()),
    default=sorted(df["Category"].unique())
)
min_date = df["Order_Date"].min().date()
max_date = df["Order_Date"].max().date()
date_range = st.sidebar.date_input(
    "Order date range", value=(min_date, max_date),
    min_value=min_date, max_value=max_date
)

filtered = df[df["Category"].isin(categories)].copy()
if isinstance(date_range, tuple) and len(date_range) == 2:
    filtered = filtered[
        (filtered["Order_Date"].dt.date >= date_range[0]) &
        (filtered["Order_Date"].dt.date <= date_range[1])
    ]

total_revenue = filtered["Revenue"].sum()
total_orders = filtered["Order_ID"].nunique()
unique_customers = filtered["Customer_ID"].nunique()
avg_order_value = total_revenue / total_orders if total_orders else 0

c1, c2, c3, c4 = st.columns(4)
c1.metric("Total Revenue", f"₹{total_revenue:,.0f}")
c2.metric("Total Orders", f"{total_orders:,}")
c3.metric("Unique Customers", f"{unique_customers:,}")
c4.metric("Avg. Order Value", f"₹{avg_order_value:,.0f}")

st.divider()

customer_summary = (
    filtered.groupby(["Customer_ID", "Customer_Name"], as_index=False)
    .agg(
        Total_Spending=("Revenue", "sum"),
        Orders=("Order_ID", "nunique"),
        Items=("Quantity", "sum"),
        Average_Order_Value=("Revenue", "mean"),
        Last_Purchase=("Order_Date", "max")
    )
)
customer_summary["Rank"] = (
    customer_summary["Total_Spending"]
    .rank(method="dense", ascending=False).astype(int)
)

st.subheader("🏆 Most Valuable Customers")
top_n = st.slider("Number of customers to display", 5, 20, 10)
top_customers = customer_summary.sort_values("Total_Spending", ascending=False).head(top_n)

st.dataframe(
    top_customers[[
        "Rank","Customer_ID","Customer_Name","Total_Spending",
        "Orders","Items","Average_Order_Value","Last_Purchase"
    ]],
    use_container_width=True,
    hide_index=True,
    column_config={
        "Total_Spending": st.column_config.NumberColumn("Total Spending", format="₹%.2f"),
        "Average_Order_Value": st.column_config.NumberColumn("Avg. Order Value", format="₹%.2f"),
        "Last_Purchase": st.column_config.DateColumn("Last Purchase")
    }
)

col1, col2 = st.columns(2)
with col1:
    fig = px.bar(
        top_customers.sort_values("Total_Spending"),
        x="Total_Spending", y="Customer_Name", orientation="h",
        title="Top Customers by Total Spending",
        labels={"Total_Spending":"Total Spending (₹)", "Customer_Name":"Customer"}
    )
    st.plotly_chart(fig, use_container_width=True)

with col2:
    fig2 = px.scatter(
        customer_summary, x="Orders", y="Total_Spending",
        size="Items", hover_name="Customer_Name",
        title="Customer Value: Orders vs Spending",
        labels={"Orders":"Number of Orders", "Total_Spending":"Total Spending (₹)"}
    )
    st.plotly_chart(fig2, use_container_width=True)

st.divider()
col3, col4 = st.columns(2)

with col3:
    category_summary = (
        filtered.groupby("Category", as_index=False)["Revenue"].sum()
        .sort_values("Revenue", ascending=False)
    )
    fig3 = px.pie(
        category_summary, names="Category", values="Revenue",
        title="Revenue Contribution by Category"
    )
    st.plotly_chart(fig3, use_container_width=True)

with col4:
    monthly = (
        filtered.assign(Month=filtered["Order_Date"].dt.to_period("M").astype(str))
        .groupby("Month", as_index=False)["Revenue"].sum()
    )
    fig4 = px.line(
        monthly, x="Month", y="Revenue", markers=True,
        title="Monthly Revenue Trend",
        labels={"Revenue":"Revenue (₹)", "Month":"Month"}
    )
    st.plotly_chart(fig4, use_container_width=True)

st.subheader("🎯 Customer Segmentation")
q1 = customer_summary["Total_Spending"].quantile(.25)
q2 = customer_summary["Total_Spending"].quantile(.50)
q3 = customer_summary["Total_Spending"].quantile(.75)

def segment(x):
    if x >= q3:
        return "VIP"
    if x >= q2:
        return "High Value"
    if x >= q1:
        return "Regular"
    return "Low Value"

customer_summary["Segment"] = customer_summary["Total_Spending"].apply(segment)
seg = customer_summary["Segment"].value_counts().rename_axis("Segment").reset_index(name="Customers")
fig5 = px.bar(seg, x="Segment", y="Customers", title="Customer Segments")
st.plotly_chart(fig5, use_container_width=True)

st.info(
    "Key insight: customers with high total spending and frequent orders are the strongest "
    "targets for retention programs, loyalty rewards and personalized offers."
)
st.caption("Customer Analysis Project | Python • Pandas • Streamlit • Plotly")

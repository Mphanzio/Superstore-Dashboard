import streamlit as st
import pandas as pd
import plotly.express as px

st.title("Superstore Sales Dashboard")

@st.cache_data
def load_data():
    df = pd.read_csv("superstore_data.csv", encoding='cp1252')
    df['Order Date'] = pd.to_datetime(df['Order Date'])
    df['Ship Date'] = pd.to_datetime(df['Ship Date'])
    return df

df = load_data()

df['Profit Margin'] = (df['Profit']/df['Sales'])*100
total_sales = df['Sales'].sum()
total_profit = df['Profit'].sum()
total_orders = df['Order ID'].nunique()

col1,col2,col3 = st.columns(3)
col1.metric("Total Sales", f"${total_sales:.2f}")
col2.metric("Total Profit", f"${total_profit:.2f}")
col3.metric("Total Orders", total_orders)

st.subheader("Raw Data Preview")
st.dataframe(df.head())

st.sidebar.header("Filter Options")

#Region Filter
regions = df['Region'].unique().tolist()
selected_region = st.sidebar.multiselect("Select Region(s):", regions, default=regions)

#Date Filter
min_date = df['Order Date'].min()
max_date = df['Order Date'].max()
date_range = st.sidebar.date_input("Select Date Range", [min_date, max_date], min_value=min_date, max_value=max_date)

#Filter the data
filtered_df = df[
    (df['Region'].isin(selected_region)) &
    (df['Order Date']>= pd.to_datetime(date_range[0])) &
    (df['Order Date']<= pd.to_datetime(date_range[1]))
]

st.subheader("Sales by Category")
category_sales = filtered_df.groupby('Category')['Sales'].sum().reset_index()
fig1 = px.bar(category_sales, x='Category', y='Sales', color='Category', title="Sales by Category")
st.plotly_chart(fig1)

#Time series
st.subheader("Monthly Sales Trend")
monthly_sales = filtered_df.resample('ME', on="Order Date")['Sales'].sum().reset_index()
fig2 = px.line(monthly_sales, x='Order Date', y='Sales', title="Sales Over Time")
st.plotly_chart(fig2)

st.subheader("Customer Segmenatation")

#Create RFM
import datetime as dt

snapshot_date = filtered_df['Order Date'].max() + dt.timedelta(days=1)

rfm = filtered_df.groupby('Customer ID').agg({
    'Order Date': lambda x: (snapshot_date - x.max()).days,
    'Order ID': 'nunique',
    'Sales' : 'sum'
}).reset_index()

rfm.columns = ['Customer ID', 'Recency', 'Frequency', 'Monetary']

rfm['R_Score'] = pd.qcut(rfm['Recency'], 4, labels=[4,3,2,1])
rfm['F_Score'] = pd.qcut(rfm['Frequency'].rank(method='first'), 4, labels=[1,2,3,4])
rfm['M_Score'] = pd.qcut(rfm['Monetary'], 4, labels=[1,2,3,4])

rfm['RFM_Segment'] = rfm['R_Score'].astype(str) + rfm['F_Score'].astype(str) + rfm['M_Score'].astype(str)
rfm['RFM_Score'] = rfm[['R_Score', 'F_Score', 'M_Score']].astype(int).sum(axis=1)

def segment_customer(score):
    if score >= 9:
        return 'Champions'
    elif score >= 7:
        return 'Loyal'
    elif score >= 5:
        return 'Potential'
    else:
        return 'At Risk'

rfm['Segment'] =rfm['RFM_Score'].apply(segment_customer)

seg_counts = rfm['Segment'].value_counts().reset_index()
seg_counts.columns = ['Segment', 'Count']
fig3 = px.pie(seg_counts, names='Segment', values='Count', title="Customer Segmentation")
st.plotly_chart(fig3)

st.write("Top 10 Customers by Monetary Value")
st.dataframe(rfm.sort_values(by='Monetary', ascending=False).head(10))

#Profit Margins
st.subheader("Profit Margins")
profit_by_product = filtered_df.groupby('Sub-Category')['Profit Margin'].mean().reset_index()
fig4 = px.bar(profit_by_product, x='Sub-Category', y='Profit Margin', color='Sub-Category', title="Profit Margins by Sub-Category")
st.plotly_chart(fig4)

profit_by_category = filtered_df.groupby('Category')['Profit Margin'].mean().reset_index()
fig5 = px.bar(profit_by_category, x='Category', y='Profit Margin', color='Category', title="Profit Margins by Category")
st.plotly_chart(fig5)

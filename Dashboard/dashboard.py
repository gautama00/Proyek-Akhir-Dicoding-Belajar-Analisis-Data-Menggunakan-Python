import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st
from babel.numbers import format_currency
sns.set(style='dark')

def create_number_of_customer_city(df):
    number_of_customer_city = df.groupby(by= "customer_city").customer_id.nunique().sort_values(ascending= False).reset_index()
    return number_of_customer_city

def create_number_of_seller_city(df):
     number_of_seller_city = df.groupby(by= "seller_city").seller_id.nunique().sort_values(ascending= False).reset_index()
     return number_of_seller_city

def create_number_of_customer_state(df):
    number_of_customer_state = df.groupby(by= "customer_state").customer_id.nunique().sort_values(ascending= False).reset_index()
    return number_of_customer_state

def create_number_of_seller_state(df):
     number_of_seller_state = df.groupby(by= "seller_state").seller_id.nunique().sort_values(ascending= False).reset_index()
     return number_of_seller_state


def create_monthly_orders_df(df):
    order_delivered = df[df["order_status"]== "delivered"]
    monthly_orders_df = order_delivered.resample(rule='M', on='order_approved_at').agg({
        "order_id":"nunique",
        "payment_value_y":"sum"
    }).sort_index()
    monthly_orders_df.index = monthly_orders_df.index.strftime('%B') #mengubah format order date menjadi Tahun-Bulan
    monthly_orders_df = monthly_orders_df.reset_index()
    monthly_orders_df.rename(columns={
        "order_id": "order_count",
        "payment_value_y":"Nominal Transaction"
    }, inplace=True)
    return monthly_orders_df

def create_lovely_product(df):
    lovely_product = df.groupby(by = "product_category_name_english").order_id.nunique().reset_index()
    return lovely_product

def create_data_for_rating_customer_service(df): 
    data_for_rating_customer_service = df.groupby(by="review_score").order_id.nunique().reset_index()
    return data_for_rating_customer_service

def create_rfm_df(df):
    rfm_df = df.groupby(by="customer_unique_id", as_index=False).agg({
    "order_approved_at": "max", #mengambil tanggal order terakhir
    "order_id": "nunique",
    "payment_value_y": "sum"
    })
    rfm_df.columns = ["customer_unique_id", "max_order_timestamp", "frequency", "monetary"]
    
    rfm_df = rfm_df.dropna(subset=["max_order_timestamp"]) # menghapus nilai kosong

    rfm_df["max_order_timestamp"] =  pd.to_datetime(rfm_df["max_order_timestamp"]) # mengubah tipe data ke datetime

    df_rfm = df[df["order_approved_at"].isna()==False]
    df_rfm.order_approved_at.isna().sum()

    # menghitung kapan terakhir pelanggan melakukan transaksi (hari)
    rfm_df["max_order_timestamp"] = rfm_df["max_order_timestamp"].dt.date
    recent_date = df_rfm["order_approved_at"].dt.date.max()
    rfm_df["recency"] = rfm_df["max_order_timestamp"].apply(lambda x: (recent_date - x).days)

    rfm_df.drop("max_order_timestamp", axis=1, inplace=True)

    # membuat rank
    rfm_df['r_rank'] = rfm_df['recency'].rank(ascending=False)
    rfm_df['f_rank'] = rfm_df['frequency'].rank(ascending=True)
    rfm_df['m_rank'] = rfm_df['monetary'].rank(ascending=True)

    # normalizing the rank of the customers
    rfm_df['r_rank_norm'] = (rfm_df['r_rank']/rfm_df['r_rank'].max())*100
    rfm_df['f_rank_norm'] = (rfm_df['f_rank']/rfm_df['f_rank'].max())*100
    rfm_df['m_rank_norm'] = (rfm_df['m_rank']/rfm_df['m_rank'].max())*100
    
    rfm_df.drop(columns=['r_rank', 'f_rank', 'm_rank'], inplace=True)

    rfm_df['RFM_score'] = 0.15*rfm_df['r_rank_norm']+0.28 * \
    rfm_df['f_rank_norm']+0.57*rfm_df['m_rank_norm']
    rfm_df['RFM_score'] *= 0.05
    rfm_df = rfm_df.round(2)

    # segmentasi customer
    rfm_df["customer_segment"] = np.where(
    rfm_df['RFM_score'] > 4.5, "Top customers", (np.where(
        rfm_df['RFM_score'] > 4, "High value customer",(np.where(
            rfm_df['RFM_score'] > 3, "Medium value customer", np.where(
                rfm_df['RFM_score'] > 1.6, 'Low value customers', 'lost customers'))))))

    customer_segment_df = rfm_df.groupby(by="customer_segment", as_index=False).customer_unique_id.nunique()

    customer_segment_df['customer_segment'] = pd.Categorical(customer_segment_df['customer_segment'], [
    "lost customers", "Low value customers", "Medium value customer",
    "High value customer", "Top customers"
    ])

    return customer_segment_df

# Load cleaned data
alldata = pd.read_csv("Dashboard/alldata.csv")

datetime_columns = ["order_purchase_timestamp", "order_approved_at", "order_delivered_carrier_date", "order_delivered_customer_date", "order_estimated_delivery_date","review_creation_date","review_answer_timestamp","shipping_limit_date"]
alldata.sort_values(by="order_approved_at", inplace=True)
alldata.reset_index(inplace=True)

for column in datetime_columns:
    alldata[column] = pd.to_datetime(alldata[column], format = 'mixed')

# Filter data
min_date = alldata["order_approved_at"].min()
max_date = alldata["order_approved_at"].max()

with st.sidebar:
    # Menambahkan logo perusahaan
    st.image("download.jpg")
    
    # Mengambil start_date & end_date dari date_input
    start_date, end_date = st.date_input(
        label='Rentang Waktu',min_value=min_date,
        max_value=max_date,
        value=[min_date, max_date]
    )

main_df = alldata[(alldata["order_approved_at"] >= str(start_date)) & 
                (alldata["order_approved_at"] <= str(end_date))]

# st.dataframe(main_df)

# # Menyiapkan berbagai dataframe
number_of_customer_city = create_number_of_customer_city(main_df)
number_of_seller_city = create_number_of_seller_city(main_df)
monthly_orders_df = create_monthly_orders_df(main_df)
data_for_rating_customer_service = create_data_for_rating_customer_service(main_df)
lovely_product = create_lovely_product(main_df)
number_of_customer_state = create_number_of_customer_state(main_df)
number_of_seller_state = create_number_of_seller_state(main_df)
customer_segment_df = create_rfm_df(main_df)

# Title
st.header("E-Commerse Dashboard :sparkles:")

# Monthly Orders
st.subheader("Monthly Orders")

total_order = monthly_orders_df["order_count"].tail(12).sum()
st.markdown(f"Total Order: **{total_order}**")

total_revenue = format_currency(monthly_orders_df["Nominal Transaction"].tail(12).sum(), "IDR", locale="id_ID")
st.markdown(f"Total Revenue: **{total_revenue}**")

fig, ax = plt.subplots(figsize=(12, 6))
ax.plot(
    monthly_orders_df["order_approved_at"].tail(12),
    monthly_orders_df["order_count"].tail(12),
    marker="o",
    linewidth=2,
)
ax.tick_params(axis="x", rotation=45)
ax.tick_params(axis="y", labelsize=15)
st.pyplot(fig)

# Monthly Orders
st.subheader("Monthly Transaction Value")

total_trans_value = format_currency(monthly_orders_df["Nominal Transaction"].tail(12).sum(), "IDR", locale="id_ID")
st.markdown(f"Total Spend: **{total_trans_value}**")

avg_trans_value = format_currency(monthly_orders_df["Nominal Transaction"].tail(12).mean(), "IDR", locale="id_ID")
st.markdown(f"Average Spend: **{avg_trans_value}**")

fig, ax = plt.subplots(figsize=(12, 6))
ax.plot(
    monthly_orders_df["order_approved_at"].tail(12),
    monthly_orders_df["Nominal Transaction"].tail(12),
    marker="o",
    linewidth=2,
)
ax.tick_params(axis="x", rotation=45)
ax.tick_params(axis="y", labelsize=15)
st.pyplot(fig)

# Top Cities by Number of Customers
st.subheader("Top Cities by Number of Customers and Sellers")

colors = ["#72BCB1", "#D3D3D3", "#D3D3D3", "#D3D3D3", "#D3D3D3"]

fig, ax = plt.subplots(nrows=1, ncols=2, figsize=(30, 14))  

sns.barplot(x="customer_id", y="customer_city", data=number_of_customer_city.head(5), palette=colors, ax=ax[0])
ax[0].set_ylabel("City", fontsize=24)
ax[0].set_xlabel("Number of Customers", fontsize=24)
ax[0].set_title("Top Cities by Number of Customers", loc="center", fontsize= 28)
ax[0].tick_params(axis='y', labelsize=22)
ax[0].tick_params(axis='x', labelsize=22)

sns.barplot(x="seller_id", y="seller_city", data=number_of_seller_city.head(5), palette=colors, ax=ax[1])
ax[1].set_ylabel("City", fontsize=24)
ax[1].set_xlabel("Number of sellers", fontsize=24)
ax[1].invert_xaxis()
ax[1].yaxis.set_label_position("right")
ax[1].yaxis.tick_right()
ax[1].set_title("Top Cities by Number of Sellers", loc="center", fontsize=28)
ax[1].tick_params(axis='y', labelsize=22)
ax[1].tick_params(axis='x', labelsize=22)

plt.tight_layout(rect=[0, 0, 1, 0.93])  
fig.subplots_adjust(hspace=0.5) 

st.pyplot(fig)

# Top States by The Number of Customer and Sellers
st.subheader("Top States by The Number of Customer and Sellers")

fig, ax = plt.subplots(nrows=1, ncols=2, figsize=(20, 14))  

sns.barplot(x="customer_id", y="customer_state", data=number_of_customer_state.head(5), palette=colors, ax=ax[0])
ax[0].set_ylabel("State", fontsize= 20)
ax[0].set_xlabel("Number of customers", fontsize=20)
ax[0].set_title("Top States by Number of customers", loc="center", fontsize=22)
ax[0].tick_params(axis='y', labelsize=16)
ax[0].tick_params(axis='x', labelsize=16)

sns.barplot(x="seller_id", y="seller_state", data=number_of_seller_state.head(5), palette=colors, ax=ax[1])
ax[1].set_ylabel("state", fontsize=20)
ax[1].set_xlabel("Number of Sellers", fontsize=20)
ax[1].invert_xaxis()
ax[1].yaxis.set_label_position("right")
ax[1].yaxis.tick_right()
ax[1].set_title("Top States by Number of Sellers", loc="center", fontsize=22)
ax[1].tick_params(axis='y', labelsize=16)
ax[1].tick_params(axis='x', labelsize=16)

plt.tight_layout(rect=[0, 0, 1, 0.93])  
fig.subplots_adjust(hspace=0.5) 

st.pyplot(fig)

# Most Interesting Product
st.subheader("Most Interesting Product")

fig = plt.figure(figsize=(10, 5))

sns.barplot(
    y="product_category_name_english", 
    x="order_id",
    data=lovely_product.sort_values(by="order_id", ascending=False).head(),
    palette=colors
)
plt.title("Most Interesting Product Categories", loc="center", fontsize=22, pad = 20)
plt.ylabel("Product Categories", fontsize = 20 )
plt.xlabel("Number of Transaction", fontsize = 20)
plt.tick_params(axis='x', labelsize=16)
plt.tick_params(axis='y', labelsize=16)

st.pyplot(fig)

# Customer Service Review Score
st.subheader("Customer Service Review Score")

fig = plt.figure(figsize=(10, 5))

sns.barplot(
    y="order_id", 
    x="review_score",
    data= data_for_rating_customer_service,
    palette= ["orange" if i == max(data_for_rating_customer_service.order_id) else 'skyblue' for i in data_for_rating_customer_service.order_id]
)
plt.title("Customer Service Review Score", loc="center", fontsize=22, pad = 20)
plt.ylabel("Rating", fontsize = 20, labelpad = 15)
plt.xlabel("Review Score", fontsize = 20, labelpad = 15)
plt.tick_params(axis='x', labelsize=16)
plt.tick_params(axis='y', labelsize=16)

st.pyplot(fig)

# Customer Segmentation
st.subheader("Customer Segmentation")

fig = plt.figure(figsize=(10, 5))

sns.barplot(
    x="customer_unique_id", 
    y="customer_segment",
    data=customer_segment_df,
    palette= ["#72BCD4" if value >= customer_segment_df.customer_unique_id.median() else "#D3D3D3" 
              for value in customer_segment_df.sort_values(by="customer_segment", ascending=True)["customer_unique_id"]]
)

plt.title("Number of Customer for Each Segment", loc="center", fontsize = 20)
plt.ylabel('Category', fontsize = 18, labelpad = 15)
plt.xlabel('Count', fontsize = 18, labelpad = 15)
plt.tick_params(axis='y', labelsize=16)
plt.tick_params(axis='x', labelsize=16)

st.pyplot(fig)
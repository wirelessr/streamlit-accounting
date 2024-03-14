from datetime import datetime, timedelta

import streamlit as st
import matplotlib.pyplot as plt
from matplotlib.font_manager import fontManager
import pymongo
from pymongo.server_api import ServerApi
from pandas import DataFrame
from mplfonts import use_font

# Initialize connection.
# Uses st.cache_resource to only run once.
@st.cache_resource
def init_connection():
    return pymongo.MongoClient(st.secrets["mongo"]["uri"], server_api=ServerApi('1'))

client = init_connection()

@st.cache_data(ttl=600)
def get_data(name, limit=10):
    db = client.dev
    items = db.accounting.find({'User': name}, {'_id': 0, 'Category': 0}).sort('_id', -1).limit(limit)
    items = list(items)
    return DataFrame(items)

@st.cache_data(ttl=600)
def get_user():
    db = client.dev
    users = db.user.find().sort('_id', -1)
    users = [x['name'] for x in users]
    return users

@st.cache_data(ttl=600)
def get_summary(user, aggr='Monthly', limit=20):
    db = client.dev
    if aggr == 'Daily':
        fmt = '%Y-%m-%d'
    else:
        fmt = '%Y-%m'
    items = db.accounting.aggregate(
        [
            {"$match": {"User": user}},
            {
                "$project": {
                    "date": {
                        "$dateToString": {
                            "format": fmt,
                            "date": {"$toDate": "$DateTime"},
                        }
                    },
                    "Amount": 1,
                }
            },
            {"$group": {"_id": "$date", "totalAmount": {"$sum": "$Amount"}}},
            {"$sort": {"_id": 1}},
            {"$limit": limit},
        ]
    )
    items = list(items)
    return DataFrame(items)

@st.cache_data(ttl=600)
def get_ratio(user, group='Item', last_days=60):
    db = client.dev
    start_date = datetime.now() - timedelta(days=last_days)
    items = db.accounting.aggregate(
        [
            {"$match": {
                "User": user,
                "DateTime": {"$gte": start_date}
                }
            },
            {
                "$project": {
                    group: 1,
                    "Amount": 1,
                }
            },
            {"$group": {"_id": f"${group}", "totalAmount": {"$sum": "$Amount"}}},
            {"$sort": {"_id": 1}},
        ]
    )
    items = list(items)
    return DataFrame(items)

user = st.selectbox('User', get_user())

d = st.date_input('Date')
t = st.time_input('Time')
item = st.text_input('Item')
amount = int(st.number_input('Amount', step=1))
category = st.selectbox('Category', ['無', '食物', '交通', '娛樂', '雜項'])

dt = datetime.combine(d, t)

if st.button('Submit') and item and amount:
    db = client.dev
    db.accounting.insert_one({'DateTime': dt, 'Item': item, 'Amount': amount, 'User': user, 'Category': category})
    st.write('Submitted')
    # Clear cache
    st.cache_data.clear()

# 設定CJK font
fonts = fontManager.get_font_names()
for font in fonts:
    if 'CJK' in font:
        use_font(font)
        break

# 折線圖匯總
aggr = st.radio("Aggregation", ['Monthly', 'Daily'], horizontal=True)
summary = get_summary(user, aggr)
#st.line_chart(summary, x='_id', y='totalAmount')

dates = summary['_id']
amounts = summary['totalAmount']
fig, ax = plt.subplots()
ax.plot(dates, amounts, marker='o', linestyle='-')
for i, txt in enumerate(amounts):
    ax.annotate(txt, (dates[i], amounts[i]), textcoords="offset points", xytext=(0, 10), ha='center')

ax.set_title(f'{aggr} Total Amount')
ax.set_ylabel('Total Amount')
ax.tick_params(axis='x', rotation=45)
st.pyplot(fig)

# 分類圓餅圖
if st.toggle('Pie Chart for Last 60 Days'):
    group = st.radio('Group by', ['Item', 'Category'], horizontal=True)
    ratio = get_ratio(user, group)
    fig, ax = plt.subplots()
    amounts = ratio['totalAmount']
    items = ratio['_id']
    labels = [f'{items[i]}: {amounts[i]}' for i in range(len(items))] 
    ax.pie(amounts, labels=labels, autopct='%1.1f%%')
    st.pyplot(fig)

# 近期消費表
items = get_data(user)
st.table(items)

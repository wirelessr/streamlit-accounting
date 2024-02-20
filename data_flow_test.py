from datetime import datetime

import streamlit as st
import pymongo
from pymongo.server_api import ServerApi
from pandas import DataFrame

# Initialize connection.
# Uses st.cache_resource to only run once.
@st.cache_resource
def init_connection():
    return pymongo.MongoClient(st.secrets["mongo"]["uri"], server_api=ServerApi('1'))

client = init_connection()

def get_data(name):
    db = client.dev
    items = db.accounting.find({'User': name}).sort('_id', -1)
    items = list(items)
    if items:
        return DataFrame(items).drop(columns=['_id'])
    else:
        return DataFrame(items)

# Pull data from the collection.
# Uses st.cache_data to only rerun when the query changes or after 10 min.
@st.cache_data(ttl=600)
def get_user():
    db = client.dev
    users = db.user.find().sort('_id', -1)
    users = [x['name'] for x in users]
    return users

user = st.selectbox('User', get_user())

d = st.date_input('Date')
t = st.time_input('Time')
item = st.text_input('Item')
amount = int(st.number_input('Amount', step=1))

dt = datetime.combine(d, t)

if st.button('Submit') and item and amount:
    db = client.dev
    db.accounting.insert_one({'DateTime': dt, 'Item': item, 'Amount': amount, 'User': user})
    st.write('Submitted')

items = get_data(user)
st.table(items)


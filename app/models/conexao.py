import streamlit as st
from mysql.connector.pooling import MySQLConnectionPool

@st.cache_resource
def obter_pool():
    return MySQLConnectionPool(
        pool_name="reservas_pool",
        pool_size=5,
        host=st.secrets["mysql"]["host"],
        port=st.secrets["mysql"]["port"],
        database=st.secrets["mysql"]["database"],
        user=st.secrets["mysql"]["user"],
        password=st.secrets["mysql"]["password"],
        ssl_ca=st.secrets["mysql"]["ssl_ca"]
    )

def conectar_banco():
    return obter_pool().get_connection()
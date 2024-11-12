import pandas as pd, streamlit as st
from sqlalchemy import create_engine

st.set_page_config(layout="wide")
st.title('The Memes By 6529')
st.header('Bid Ask TimeSeries')

#Users
db_user = st.secrets['db_user']
db_pw = st.secrets['db_pw']
db_host = st.secrets['db_host']
db_port = st.secrets['db_port']
db = st.secrets['db']

#SQL & ETH Connections
sql_engine = create_engine(f"mysql+mysqlconnector://{db_user}:{db_pw}@{db_host}:{db_port}/{db}", pool_recycle=3600, pool_pre_ping=True)
sql_engine = sql_engine.execution_options(autocommit=True)

df=pd.read_sql("""               
SELECT 
BIDASKS.TimeStamp
, sum(CASE WHEN BIDASKS.Bid < NAKA.Bid THEN BIDASKS.Bid ELSE 0 END) as Bid
, sum(CASE WHEN BIDASKS.Ask < NAKA.Ask THEN BIDASKS.Ask ELSE 0 END) as Ask
FROM 
    thememes6529.bidasks BIDASKS

JOIN 
    thememes6529.bidasks NAKA
    on BIDASKS.TimeStamp = NAKA.TimeStamp
    and NAKA.TokenID = 4
               
WHERE BIDASKS.TimeStamp in (SELECT MAX(TimeStamp) FROM thememes6529.bidasks GROUP BY DATE(TimeStamp))
GROUP BY BIDASKS.TimeStamp
ORDER by BIDASKS.TimeStamp""", sql_engine)

st.line_chart(df, x="TimeStamp",y=["Bid","Ask"], height=666, use_container_width=True)

sql_engine.dispose()
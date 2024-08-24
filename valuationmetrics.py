import pandas as pd, streamlit as st
from sqlalchemy import create_engine

st.title('The Memes By 6529')
st.header('Valuation')

#Users
db_user = st.secrets['db_user']
db_pw = st.secrets['db_pw']
db_host = st.secrets['db_host']
db_port = st.secrets['db_port']
db = st.secrets['db']

#SQL & ETH Connections
sql_engine = create_engine(f"mysql+mysqlconnector://{db_user}:{db_pw}@{db_host}:{db_port}/{db}", pool_recycle=3600, pool_pre_ping=True)
sql_engine = sql_engine.execution_options(autocommit=True)

df=pd.read_sql("""SELECT 
STATS.Szn	
, BIDASKS.TokenID
, STATS.TokenName
, BIDASKS.Bid
, BIDASKS.Ask
, BIDASKS.Bid / BIDASKS.Ask as BidAskRatio
, STATS.Points
, STATS.TDHWeight
, STATS.Points/BIDASKS.Ask as PointsAskRatio
, STATS.TDHWeight/BIDASKS.Ask as TDHWeightAskRatio
FROM thememes6529.bidasks BIDASKS
LEFT JOIN thememes6529.stats STATS
ON BIDASKS.TokenID = STATS.TokenID
WHERE BIDASKS.TimeStamp = (SELECT MAX(TimeStamp) FROM thememes6529.bidasks)""", sql_engine)

st.dataframe(df, use_container_width=True, hide_index=True, height=666)

sql_engine.dispose()
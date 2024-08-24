import pandas as pd, streamlit as st
from sqlalchemy import create_engine

st.title('OMGBot')

#Users
db_user = st.secrets['db_user']
db_pw = st.secrets['db_pw']
db_host = st.secrets['db_host']
db_port = st.secrets['db_port']
db = st.secrets['db']

#SQL & ETH Connections
sql_engine = create_engine(f"mysql+mysqlconnector://{db_user}:{db_pw}@{db_host}:{db_port}/{db}", pool_recycle=3600, pool_pre_ping=True)
sql_engine = sql_engine.execution_options(autocommit=True)

#Date and investment
ethinvestment=pd.read_sql("""SELECT sum(InvestmentETH) as InvestmentETH FROM thememes6529.investors""",sql_engine).InvestmentETH.iloc[0]

#Data
df=pd.read_sql("""SELECT BIDASKS.TimeStamp
, ETHWETH.ETHWETHBal + sum(BIDASKS.TokenBal * BIDASKS.Bid) as NAVBid
, ETHWETH.ETHWETHBal + sum(BIDASKS.TokenBal * BIDASKS.Ask) as NAVAsk 
FROM thememes6529.bidasks BIDASKS
LEFT JOIN thememes6529.ethweth ETHWETH
ON BIDASKS.TimeStamp = ETHWETH.TimeStamp
WHERE BIDASKS.TimeStamp >= '2023-04-06 14:03:54'
and BIDASKS.TimeStamp in (select max(TimeStamp) from thememes6529.bidasks group by Date(TimeStamp))
group by BIDASKS.TimeStamp, ETHWETH.ETHWETHBal""", sql_engine)

#Calc Returns
max_ts = df.TimeStamp.max()
navbid = df[df.TimeStamp == max_ts].NAVBid.iloc[0]
navask = df[df.TimeStamp == max_ts].NAVAsk.iloc[0]
returnsbid = round(navbid / ethinvestment - 1,2)
returnsask = round(navask / ethinvestment - 1,2)

bidcol, askcol = st.columns(2)
bidcol.subheader(f"Bid returns: {returnsbid}%")
askcol.subheader(f"Ask returns: {returnsask}%")

#Chart
st.line_chart(df, x="TimeStamp",y=["NAVBid","NAVAsk"], height=666)

sql_engine.dispose()
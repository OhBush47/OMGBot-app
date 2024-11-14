import pandas as pd, altair as alt, streamlit as st
from sqlalchemy import create_engine

st.set_page_config(layout="wide")
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
investment=pd.read_sql("""SELECT sum(InvestmentETH) as InvestmentETH FROM thememes6529.investors""",sql_engine).InvestmentETH.iloc[0]

#Data
df=pd.read_sql("""SELECT BIDASKS.TimeStamp
, ETHWETH.ETHBal + ETHWETH.WETHBal as ETHWETH
, ETHWETH.OTHERBal as COINS
, sum(BIDASKS.TokenBal * BIDASKS.Ask) as NFTS
FROM thememes6529.bidasks BIDASKS
LEFT JOIN thememes6529.ethweth ETHWETH
ON BIDASKS.TimeStamp = ETHWETH.TimeStamp
WHERE BIDASKS.TimeStamp >= '2023-04-06 14:03:54'
and BIDASKS.TimeStamp in (select max(TimeStamp) from thememes6529.bidasks group by Date(TimeStamp))
group by BIDASKS.TimeStamp, ETHWETH.ETHBal, ETHWETH.WETHBal, ETHWETH.OTHERBal""", sql_engine)
df.fillna(0,inplace=True)

#Calc Returns
max_ts = df.TimeStamp.max()
nav = df[df.TimeStamp == max_ts][['ETHWETH','COINS','NFTS']].sum(axis=1)
st.write(nav)
returns = nav / investment - 1
returns *= 100

#Melt
df_melted = df.melt('TimeStamp', var_name='Asset', value_name='ETH')

#Metrics
st.subheader(f"Returns: {round(returns,2)}%")

#Chart
chart = alt.Chart(df_melted).mark_bar().encode(
    x=alt.X('TimeStamp', title='TimeStamp'),
    y=alt.Y('sum(ETH)', title='ETH'),
    color='Asset'
).properties(
    width=200
)
st.altair_chart(chart, use_container_width=True)

sql_engine.dispose()
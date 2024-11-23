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
investment=pd.read_sql("""SELECT sum(InvestmentETH) as InvestmentETH FROM thememes6529.investors where ENS != 'trading.chrisroc.eth'""",sql_engine).InvestmentETH.iloc[0]

def Chart(bidask):
    #Data
    df=pd.read_sql(f"""SELECT BIDASKS.TimeStamp
    , ETHWETH.ETHBal + ETHWETH.WETHBal as ETHWETH
    , ETHWETH.OTHERBal as COINS
    , sum(BIDASKS.TokenBal * BIDASKS.{bidask}) as NFTS
    FROM thememes6529.bidasks BIDASKS
    LEFT JOIN thememes6529.ethweth ETHWETH
    ON BIDASKS.TimeStamp = ETHWETH.TimeStamp
    WHERE BIDASKS.TimeStamp >= '2023-04-06 14:03:54'
    and BIDASKS.TimeStamp in (select max(TimeStamp) from thememes6529.bidasks group by Date(TimeStamp))
    group by BIDASKS.TimeStamp, ETHWETH.ETHBal, ETHWETH.WETHBal, ETHWETH.OTHERBal""", sql_engine)

    #Returns
    max_ts = df.TimeStamp.max()
    nav = df[df.TimeStamp == max_ts][['ETHWETH','COINS','NFTS']].sum(axis=1).iloc[0]
    returns = nav / investment - 1
    returns *= 100
    navcol, returnscol = st.columns(2)
    navcol.subheader(f"{bidask} NAV: {round(nav,2)}ETH")
    returnscol.subheader(f"{bidask} Returns: {round(returns,2)}%")

    #Chart
    df_melted = df.melt('TimeStamp', var_name='Asset', value_name='ETH')
    chart = alt.Chart(df_melted).mark_bar().encode(
        x=alt.X('yearmonthdate(TimeStamp):O', title='TimeStamp'),
        y=alt.Y('sum(ETH)', title='ETH'),
        color='Asset'
    ).properties(
        width=200
    )
    st.altair_chart(chart, use_container_width=True)

Chart('Bid')
Chart('Ask')

sql_engine.dispose()
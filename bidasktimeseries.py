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

#Get szns & tokens
szns = pd.read_sql("SELECT DISTINCT Szn FROM thememes6529.stats", sql_engine).Szn.tolist()
tokens = pd.read_sql("SELECT DISTINCT TokenID FROM thememes6529.stats", sql_engine).TokenID.tolist()

col_szns, col_tokens = st.columns(2)
box_szns = col_szns.multiselect("Szns:",szns)
box_tokens = col_tokens.multiselect("Tokens",tokens)
select_szns = ", ".join(box_szns)
select_tokens =", ".join(box_tokens)
st.write(select_szns)
st.write(select_tokens)

df=pd.read_sql(f"""               
SELECT 
    BIDASKS.TimeStamp
    , sum(CASE WHEN BIDASKS.Avg < NAKA.Avg THEN BIDASKS.Avg ELSE 0 END) as Avg
    , sum(CASE WHEN BIDASKS.Bid < NAKA.Bid THEN BIDASKS.Bid ELSE 0 END) as Bid
    , sum(CASE WHEN BIDASKS.Ask < NAKA.Ask THEN BIDASKS.Ask ELSE 0 END) as Ask

FROM 
    thememes6529.bidasks BIDASKS

JOIN 
    thememes6529.bidasks NAKA
    on BIDASKS.TimeStamp = NAKA.TimeStamp
    and NAKA.TokenID = 4
               
JOIN 
    thememes6529.stats STATS
    on BIDASKS.TokenID = STATS.TokenID
               
WHERE 
    STATS.Szn in ('{select_szns}')
    AND STATS.TokenID in ('{select_tokens}')

    BIDASKS.TimeStamp in (SELECT MAX(TimeStamp) FROM thememes6529.bidasks GROUP BY DATE(TimeStamp))
    GROUP BY BIDASKS.TimeStamp
    ORDER by BIDASKS.TimeStamp
""", sql_engine)

st.line_chart(df, x="TimeStamp",y=["Bid","Ask","Avg"], height=666, use_container_width=True)

sql_engine.dispose()
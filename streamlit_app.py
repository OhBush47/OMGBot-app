import streamlit as st

st.logo("omg.jpg")

pg_valuationmetrics = st.Page("bidasktable.py", title="Bid Ask Table")
pg_bidaskts = st.Page("bidaskchart.py", title="Bid Ask Chart")
pg_omgbot = st.Page("OMGBot.py", title="OMGBot")
pg_copytrader = st.Page("CopyTrader.py", title="CopyTrader")

pg = st.navigation(
    {
        "The Memes by 6529": [pg_valuationmetrics, pg_bidaskts],
        "OMGBot": [pg_omgbot],
        "Copy Trader": [pg_copytrader]
    }
)

pg.run()
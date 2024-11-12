import streamlit as st

st.logo("omg.jpg")

pg_valuationmetrics = st.Page("valuationmetrics.py", title="Valuation Metrics")
pg_bidaskts = st.Page("bidasktimeseries.py", title="Bid Ask TimeSeries")
pg_omgbot = st.Page("OMGBot.py", title="OMGBot")

pg = st.navigation(
    {
        "The Memes by 6529": [pg_valuationmetrics, pg_bidaskts],
        "OMGBot": [pg_omgbot]
    }
)

pg.run()
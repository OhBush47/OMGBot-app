import streamlit as st

pg_valuation = st.Page("valuation.py", title="Valuation")
pg_avgdaybidask = st.Page("avgdaybidask.py", title="Average Daily Bid Ask")
pg_omgbot = st.Page("OMGBot.py", title="OMGBot")

pg = st.navigation(
    {
        "The Memes by 6529": [pg_valuation, pg_avgdaybidask],
        "OMGBot": [pg_omgbot]
    }
)

pg.run()
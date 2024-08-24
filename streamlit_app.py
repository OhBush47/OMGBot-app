import streamlit as st

pg_thememesby6529 = st.Page("thememesby6529.py", title="The Memes By 6529")
pg_omgbot = st.Page("omgbot.py", title="OMGBot")

pg = st.navigation(
    {
        "The Memes by 6529": [pg_thememesby6529],
        "OMGBot": [pg_omgbot]
    }
)

pg.run()
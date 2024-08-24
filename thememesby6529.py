import streamlit as st

pg_thememesby6529 = st.Page("thememesby6529.py", title="The Memes By 6529")

pg = st.navigation(
    {
        "The Memes by 6529": [pg_thememesby6529]
    }
)

pg.run()
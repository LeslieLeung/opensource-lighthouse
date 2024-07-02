import streamlit as st

st.set_page_config(
    page_title="opensource-lighthouse",
    page_icon="👋",
)

pg = st.navigation(
    [
        st.Page(page="pages/readme.py", title="README", icon="📄"),
        st.Page(page="pages/repo.py", title="项目", icon="📦"),
        st.Page(page="pages/company.py", title="公司", icon="🏢"),
    ]
)

pg.run()

import streamlit as st
import pandas as pd

path_to_company_data = "data/display_data/companies.csv"
company_data = pd.read_csv(path_to_company_data)

st.markdown("# 公司数据")
st.dataframe(
    company_data,
    use_container_width=True,
    hide_index=True,
    column_config={
        "company": st.column_config.Column("公司"),
        "total_projects": st.column_config.Column("项目数"),
        "total_teams": st.column_config.Column("团队数"),
        "total_stars": st.column_config.Column("总 Star 数"),
        "top_3_languages": st.column_config.Column("Top 3 语言"),
        "active_projects": st.column_config.Column("活跃项目数"),
    },
)

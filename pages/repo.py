import streamlit as st
from streamlit_extras.dataframe_explorer import dataframe_explorer
import pandas as pd

path_to_repo_data = "data/repos.csv"
repo_data = pd.read_csv(path_to_repo_data)

st.markdown("# 项目数据")
filtered = dataframe_explorer(repo_data, case=False)

st.dataframe(
    filtered,
    use_container_width=True,
    hide_index=True,
    column_config={
        "id": st.column_config.Column("ID"),
        "owner": st.column_config.Column("所有者"),
        "repo": st.column_config.Column("项目"),
        "link": st.column_config.Column("链接"),
        "description": st.column_config.Column("描述"),
        "stars": st.column_config.Column("Star 数"),
        "license": st.column_config.Column("许可证"),
        "language": st.column_config.Column("语言"),
        "created_at": st.column_config.Column("创建时间"),
        "last_updated_at": st.column_config.Column("最后更新时间"),
        "company": st.column_config.Column("公司"),
    },
)

import streamlit as st

from pages import home, matrix, analytics

st.set_page_config(
    page_title="Road Access Closure Permit",
    layout="wide",
)

pages = [
    st.Page(home.render_home, title="Home"),
    st.Page(matrix.render_matrix, title="Table View"),
    st.Page(analytics.render_pdf, title="PDF View"),
]

navigation = st.navigation(pages, position="sidebar")
navigation.run()

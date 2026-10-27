import streamlit as st

from pages import home, matrix, analytics
from utils.apis import _load_matrix_df

df = _load_matrix_df()
regions = df['REGION_NAME'].unique().to_list()
streets = df['ROAD_NAME'].unique().to_list()
if "selected_region" not in st.session_state:
    st.session_state.selected_region = None
if "selected_road" not in st.session_state:
    st.session_state.selected_street = None
if "raw_data" not in st.session_state:
    st.session_state.raw_data = df.clone()

selected_regions = st.sidebar.selectbox('Select Region', regions, index=None, placeholder="Select Region...", key="region_select")
if selected_regions:
    st.session_state.selected_region = selected_regions
    # st.rerun()

st.set_page_config(
    page_title="Road Access Closure Permit - General Access Time",
    layout="wide",
)

pages = [
    st.Page(home.render_home, title="Home"),
    st.Page(matrix.render_matrix, title="Table View"),
    st.Page(analytics.render_pdf, title="PDF View"),
]

navigation = st.navigation(pages, position="sidebar")
navigation.run()

import streamlit as st

def get_all_server_locations(filepath: str) -> list:
    """Function to get all of the server locations from a file"""

# Sets the page configuration
st.set_page_config(page_title="Server Status Dashboard", layout="wide")
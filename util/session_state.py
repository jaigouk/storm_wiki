import streamlit as st


def clear_other_page_session_state(page_index: int):
    if page_index is None:
        keys_to_delete = [
            key for key in st.session_state if key.startswith("page")]
    else:
        keys_to_delete = [
            key
            for key in st.session_state
            if key.startswith("page") and f"page{page_index}" not in key
        ]
    for key in set(keys_to_delete):
        del st.session_state[key]

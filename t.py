import streamlit as st
import time
from streamlit_autorefresh import st_autorefresh

st.set_page_config(layout="wide")

SPLASH_DURATION = 5  # seconds
video_url = "https://raw.githubusercontent.com/Alsayed-101/tst1/main/intro.mp4"

# Session state to track splash status
if "show_splash" not in st.session_state:
    st.session_state.show_splash = True
    st.session_state.splash_start_time = time.time()

# If splash screen is active
if st.session_state.show_splash:
    # Show fullscreen video
    st.markdown(f"""
    <video style="position:fixed; top:0; left:0; width:100vw; height:100vh; object-fit:cover;" autoplay muted playsinline>
      <source src="{video_url}" type="video/mp4" />
    </video>
    """, unsafe_allow_html=True)

    # Auto-refresh the page every 500ms
    st_autorefresh(interval=500, key="splashrefresher")

    # Check time elapsed
    if time.time() - st.session_state.splash_start_time > SPLASH_DURATION:
        st.session_state.show_splash = False
        st.rerun()  # this works in newer versions

# If splash is done, show chatbot UI
else:
    st.title("🤖 Chatbot Loaded!")
    st.write("Now you can render the chatbot interface here.")

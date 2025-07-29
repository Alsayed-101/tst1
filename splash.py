import streamlit as st
import time

st.set_page_config(layout="wide")

video_url = "https://raw.githubusercontent.com/Alsayed-101/tst1/main/intro.mp4"

# Display fullscreen video splash
st.markdown(f"""
<style>
  body, html {{
    margin: 0; padding: 0; overflow: hidden;
  }}
  video {{
    position: fixed;
    top: 0; left: 0;
    width: 100vw;
    height: 100vh;
    object-fit: cover;
    z-index: 100;
  }}
</style>
<video autoplay muted playsinline id="intro_video">
  <source src="{video_url}" type="video/mp4" />
</video>
""", unsafe_allow_html=True)

# Delay for the video duration or fixed seconds, then redirect
time.sleep(10)  # adjust this to your video length

# Redirect user to main app
js_redirect = """
<script>
  window.location.href = "/Users/judealsayed/Desktop/adgm2/app3.py";  // or the URL/path of your main app
</script>
"""
st.markdown(js_redirect, unsafe_allow_html=True)

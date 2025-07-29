import streamlit as st
import json
import numpy as np
import requests
import os
from openai import AzureOpenAI
import gdown
import base64

def download_vectors():
    filename = "adgm_vectors.json"
    if not os.path.exists(filename):
        url = "https://drive.google.com/uc?id=1WbL0fCfochPlRGZy0kV4UNMcoW367NH_"
        print(f"Downloading {filename}...")
        gdown.download(url, filename, quiet=False)
        print("Download complete!")
    else:
        print(f"{filename} already exists locally.")

download_vectors()
# --- CONFIG ---
subscription_key = st.secrets["subscription_key"]
azure_endpoint = st.secrets["azure_endpoint"]
api_version = st.secrets["api_version"]
deployment = st.secrets["deployment"]
embedding_deployment = "text-embedding-3-large"  # Embedding deployment name

st.set_page_config(page_title="ADGM Chatbot", layout="centered")

def get_base64_of_bin_file(bin_file):
    with open(bin_file, "rb") as f:
        data = f.read()
    return base64.b64encode(data).decode()

bg_image = get_base64_of_bin_file("bg.png")
# --- CSS ---
# --- CSS ---
st.markdown(
    f"""
    <style>
    html, body, [data-testid="stAppViewContainer"], [data-testid="stVerticalBlock"] {{
        background: url("data:image/png;base64,{bg_image}") no-repeat center center fixed;
        background-size: cover;
        height: 100vh !important;
        overflow: hidden !important;
        margin: 0;
        padding: 0;
    }}

    .chat-container {{
        max-width: 720px;
        height: calc(75vh - 100px);
        margin: 0 auto;
        padding: 20px 20px 0 20px;
        border-radius: 12px 12px 0 0;
        background: rgba(255, 255, 255, 0.95);
        box-shadow: 0 8px 24px rgba(0,0,0,0.1);
        overflow-y: auto;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        scroll-behavior: smooth;
        display: flex;
        flex-direction: column;
    }}

    .welcome-text {{
        font-weight: 700;
        font-size: 1.6rem;
        color: #444;
        margin: auto;
        text-align: center;
        user-select: none;
    }}

    .user-msg {{
        background-color: #098AFF;
        color: #ffffff;
        padding: 14px 20px;
        border-radius: 24px 24px 0 24px;
        max-width: 70%;
        margin-left: auto;
        margin-bottom: 8px;
        font-size: 1.05rem;
        line-height: 1.5;
        word-wrap: break-word;
        box-shadow: 0 4px 12px rgba(9, 138, 255, 0.4);
    }}

    .bot-msg {{
        background-color: #f1f3f5;
        color: #111827;
        padding: 18px 24px;
        border-radius: 24px;
        width: 100%;
        margin-bottom: 8px;
        font-size: 1.1rem;
        line-height: 1.6;
        word-wrap: break-word;
        box-shadow: 0 4px 12px rgba(0,0,0,0.08);
    }}

    .input-area {{
        background-color: white;
        max-width: 720px;
        padding: 12px 20px;
        margin: 0 auto;
        border-radius: 0 0 12px 12px;
        display: flex;
        gap: 8px;
        align-items: center;
        box-shadow: none !important;
        border: none !important;
    }}

    /* Fix border for actual text input */
    .stTextInput > div > input {{
        height: 36px !important; 
        border-radius: 20px !important;
        padding: 0 14px !important;
        font-size: 1rem !important;
        width: 100% !important;
        margin: 0 !important;
    }}

    /* Remove button border and shadow */
    .stButton button {{
        height: 36px !important;
        padding: 6px 20px !important;
        font-size: 1rem !important;
        border-radius: 20px !important;
        background-color: #098AFF !important;
        color: #098AFF  !important;
        border: none !important;
        box-shadow: none !important;
        display: inline-block !important;
        margin-top: 4px;
    }}

    .stButton button:hover {{
        background-color: #066FD6 !important;
    }}

    .stForm > div {{
        background-color: white;
        max-width: 720px;
        padding: 8px 16px;
        margin: 0 auto;
        border-radius: 0 0 12px 12px;
        display: flex;
        flex-direction: column;
        gap: 3px;
        align-items: center;
        text-align: center;   /* c
        box-shadow: none !important;
        border: none !important;
    }}

    .css-1cpxqw2, .stSpinner > div > div {{
        color: white !important;
    }}
    </style>
    """,
    unsafe_allow_html=True
)


# --- LOAD VECTOR STORE ---
@st.cache_data(show_spinner=True)
def load_vectors():
    with open("adgm_vectors.json", "r") as f:
        return json.load(f)

vector_data = load_vectors()

# --- OPENAI CLIENT SETUP ---
client = AzureOpenAI(
    api_key=subscription_key,
    api_version=api_version,
    azure_endpoint=azure_endpoint
)

# --- UTILS ---
def cosine_similarity(a, b):
    a = np.array(a)
    b = np.array(b)
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

def get_embedding(text):
    response = client.embeddings.create(
        model=embedding_deployment,
        input=text
    )
    return response.data[0].embedding


def find_similar_chunks(query, k=3):
    query_emb = get_embedding(query)
    similarities = []
    for item in vector_data:
        sim = cosine_similarity(query_emb, item["embedding"])
        similarities.append((sim, item["text"]))
    similarities.sort(key=lambda x: x[0], reverse=True)
    return [text for _, text in similarities[:k]]

def generate_response(user_question):
    context_chunks = find_similar_chunks(user_question, k=3)
    context = "\n\n---\n\n".join(context_chunks)

    system_prompt = (
        "You are an AI-powered customer service assistant specifically designed for Abu Dhabi Global Market (ADGM). "
        "Use the following context from official ADGM sources to answer the question accurately, clearly, and formally.\n\n"
        "if asked about adgm academy anwser questions and direct users form and to this link https://www.adgmacademy.com"
        "if you dont know the anwser to an adgm specific question give users this number to contact adgm support team +971 2 333 8888 and this email info@adgm.com  "
        "ONLY if asked about Jurisdiction include al reem island not only al maryah include info from this :  Al Reem Island is now part of ADGM’s expanded business district and ADGM is working with the Reem Island business community to support the transition to an ADGM licence.ADGM is assisting existing Al Reem businesses with their transition to an ADGM licence ahead of the deadline, by exempting qualifying businesses from paying any commercial licence fees if they transition by the 31st October 2024. To continue to operate on Al Reem, businesses must transition to an ADGM licence to continue their operations after the transition period ends on the 31st December 2024. for more info visit this website  "
        "if anwser is long and in a paragraph make key information in bold , try using lists and bullets for longer anwsers"
        f"Context:\n{context}"
    )

    messages = [{"role": "system", "content": system_prompt}]
    for user, bot in st.session_state.chat_history:
        messages.append({"role": "user", "content": user})
        messages.append({"role": "assistant", "content": bot})
    messages.append({"role": "user", "content": user_question})

    response = client.chat.completions.create(
        model=deployment,
        messages=messages,
        max_tokens=800,
        temperature=0.3,
    )
    return response.choices[0].message.content.strip()


# --- APP STATE ---
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# --- UI ---
chat_placeholder = st.empty()

def render_chat():
    chat_html = '<div class="chat-container">'
    if not st.session_state.chat_history:
        chat_html += '<div class="welcome-text">Welcome to ADGM’s Virtual Assistant</div>'
    else:
        for user_msg, bot_msg in st.session_state.chat_history:
            chat_html += f'<div class="user-msg">{user_msg}</div>'
            chat_html += f'<div class="bot-msg">{bot_msg}</div>'
    chat_html += '</div>'
    chat_placeholder.markdown(chat_html, unsafe_allow_html=True)

render_chat()

with st.form("chat_form", clear_on_submit=True):
    user_input = st.text_input("", placeholder="Ask your question here...", key="input_text")
    submitted = st.form_submit_button("Send")

if submitted and user_input.strip():
    with st.spinner("Thinking..."):
        answer = generate_response(user_input.strip())
    st.session_state.chat_history.append((user_input.strip(), answer))
    render_chat()

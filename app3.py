import streamlit as st
import json
import numpy as np
import requests
import os
from openai import AzureOpenAI

def download_vectors():
    filename = "adgm_vectors.json"
    if not os.path.exists(filename):
        url = "https://drive.google.com/uc?export=download&id=1WbL0fCfochPlRGZy0kV4UNMcoW367NH_"
        print(f"Downloading {filename}...")
        response = requests.get(url)
        response.raise_for_status()  # ensure it downloaded correctly
        with open(filename, "wb") as f:
            f.write(response.content)
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

# --- CSS ---
st.markdown("""
<style>
    /* Container with light grey background */
    .chat-container {
        max-width: 720px;
        height: 480px;
        margin: 30px auto;
        padding: 24px 28px;
        border-radius: 12px;
        background: #f5f5f7; /* Light grey */
        box-shadow: 0 8px 24px rgba(0,0,0,0.1);
        overflow-y: auto;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        scroll-behavior: smooth;
        display: flex;
        flex-direction: column;
    }

    /* Welcome text in chat container */
    .welcome-text {
        font-weight: 700;
        font-size: 1.6rem;
        color: #444;
        margin: auto;
        text-align: center;
        user-select: none;
    }

    /* User message bubble */
    .user-msg {
        background-color: #16A9E9;
        color: #ffffff;
        padding: 14px 20px;
        border-radius: 24px 24px 0 24px;
        max-width: 70%;
        margin-left: auto;
        margin-bottom: 16px;
        font-size: 1.05rem;
        line-height: 1.5;
        word-wrap: break-word;
        box-shadow: 0 4px 12px rgba(22, 169, 233, 0.4);
    }

    /* Bot message bubble */
    .bot-msg {
        background-color: #f1f3f5;
        color: #111827;
        padding: 14px 20px;
        border-radius: 24px 24px 24px 0;
        max-width: 70%;
        margin-right: auto;
        margin-bottom: 16px;
        font-size: 1.05rem;
        line-height: 1.5;
        word-wrap: break-word;
        box-shadow: 0 4px 12px rgba(0,0,0,0.08);
    }

    /* Logo */
    .logo {
        display: block;
        margin-left: auto;
        margin-right: auto;
        width: 130px;
        margin-top: 12px;
        margin-bottom: 12px;
    }

    /* Input area */
    .input-area {
        max-width: 720px;
        margin: 20px auto 40px auto;
        display: flex;
        gap: 12px;
        padding: 0 8px;
    }
    .input-area input[type="text"] {
        flex-grow: 1;
        padding: 14px 20px;
        font-size: 1.1rem;
        border-radius: 28px;
        border: 1.5px solid #ccc;
        outline: none;
        transition: border-color 0.3s ease;
    }
    .input-area input[type="text"]:focus {
        border-color: #16A9E9;
        box-shadow: 0 0 6px rgba(22,169,233,0.5);
    }
    .input-area button {
        background-color: #16A9E9;
        border: none;
        color: white;
        padding: 14px 28px;
        font-size: 1.1rem;
        border-radius: 28px;
        cursor: pointer;
        transition: background-color 0.3s ease;
        box-shadow: 0 4px 12px rgba(22,169,233,0.35);
    }
    .input-area button:hover {
        background-color: #0f7abf;
        box-shadow: 0 6px 16px rgba(15,122,191,0.6);
    }
</style>
""", unsafe_allow_html=True)

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
st.image("company_logo.png", width=200)

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
    col1, col2 = st.columns([8,1])
    with col1:
        user_input = st.text_input("", placeholder="Ask your question here...", key="input_text")
    with col2:
        submitted = st.form_submit_button("Send")

if submitted and user_input.strip():
    with st.spinner("Thinking..."):
        answer = generate_response(user_input.strip())
    st.session_state.chat_history.append((user_input.strip(), answer))
    render_chat()
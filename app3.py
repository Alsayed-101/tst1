import streamlit as st
from openai import AzureOpenAI
from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential

search_endpoint = st.secrets["search_endpoint"]
search_key = st.secrets["search_key"]
search_index = st.secrets["search_index"]

search_client = SearchClient(
    endpoint=search_endpoint,
    index_name=search_index,
    credential=AzureKeyCredential(search_key)
)

# --- CONFIG ---
subscription_key = st.secrets["subscription_key"]
azure_endpoint = st.secrets["azure_endpoint"]
api_version = st.secrets["api_version"]
deployment = st.secrets["deployment"]

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

# --- OPENAI CLIENT ---
client = AzureOpenAI(
    api_key=subscription_key,
    azure_endpoint=azure_endpoint,
    api_version=api_version,
)

def get_system_prompt():
    return (
        "You are an AI assistant for Abu Dhabi Global Market (ADGM). "
        "You must only use the information provided in the context below to answer. "
        "If you are unsure or the answer is not in the provided context, say 'I don’t know based on the available information.'"
    )
def search_azure(query, top_k=3):
    results = search_client.search(query, top=top_k)
    snippets = []
    for result in results:
        # Change 'content' to your indexed text field name
        snippets.append(result.get('content', ''))
    return "\n\n".join(snippets)

def generate_response(user_question):
    # Search Azure Cognitive Search first
    search_results = search_azure(user_question)
    # 💾 Save it to session_state for later display
    st.session_state.last_search_results = search_results
    
    system_prompt = get_system_prompt() + "\n\nHere is some context from ADGM official documents:\n" + search_results
    
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


if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# Logo at top outside container (optional)
st.image("company_logo.png", width=200)

# Chat container placeholder
chat_placeholder = st.empty()

def render_chat():
    chat_html = '<div class="chat-container">'
    if not st.session_state.chat_history:
        # Show welcome text before first message
        chat_html += '<div class="welcome-text">Welcome to ADGM’s Virtual Assistant</div>'
    else:
        # Show chat messages
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
        # Generate response and get search context
        user_question = user_input.strip()
        search_context = search_azure(user_question)  # Get snippets
        answer = generate_response(user_question)
    
    # Save chat
    st.session_state.chat_history.append((user_question, answer))
    render_chat()
    
    # Show ADGM sources
    st.markdown("### Sources used from ADGM documents:")
    st.markdown(f"```\n{search_context}\n```")


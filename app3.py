import streamlit as st
from openai import AzureOpenAI

# --- CONFIG ---
subscription_key = st.secrets["subscription_key"]
azure_endpoint = st.secrets["azure_endpoint"]
api_version = st.secrets["api_version"]
deployment = st.secrets["deployment"]

# --- PAGE SETTINGS ---
st.set_page_config(page_title="ADGM Chatbot", layout="centered")

# --- CSS STYLING ---
st.markdown("""
    <style>
        .chat-container {
            max-width: 700px;
            margin: 0 auto;
        }
        .user-msg {
            background-color: #d0e7ff;
            padding: 12px;
            border-radius: 10px;
            margin-bottom: 8px;
            text-align: right;
        }
        .bot-msg {
            background-color: #f0f0f0;
            padding: 12px;
            border-radius: 10px;
            margin-bottom: 15px;
            text-align: left;
        }
    </style>
""", unsafe_allow_html=True)

# --- LOGO ---
st.markdown('<div style="text-align: center;">', unsafe_allow_html=True)
st.image("company_logo.png", use_container_width=True)
st.markdown('</div>', unsafe_allow_html=True)

# --- HEADER ---
st.title("Welcome to ADGM Chatbot")

# --- SESSION STATE ---
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "welcomed" not in st.session_state:
    st.session_state.welcomed = False
if "last_input" not in st.session_state:
    st.session_state.last_input = ""

# --- INIT OPENAI CLIENT ---
client = AzureOpenAI(
    api_key=subscription_key,
    azure_endpoint=azure_endpoint,
    api_version=api_version,
)

# --- SYSTEM PROMPT ---
def get_system_prompt():
    return (
        "You are an AI-powered customer service assistant specifically designed for Abu Dhabi Global Market (ADGM). "
        "Your role is to provide accurate, clear, and formal information to ADGM customers and visitors based solely on the official ADGM website content provided below.\n\n"
        "Instructions:\n"
        "1. On the first user interaction, start your response with a warm and welcoming statement, clearly introducing yourself as an AI chatbot assistant. Example:\n"
        "\"Hello! I’m the ADGM virtual assistant, here to help answer your questions and provide accurate information about Abu Dhabi Global Market.\"\n"
        "2. For all subsequent interactions, respond in a formal, polite, and professional tone without repeating the welcome.\n\n"
        "Responsibilities:\n"
        "- Use only ADGM content\n"
        "- Quote website references\n"
        "- If unsure: 'Please contact ADGM at 02 333 8888 or email contact@adgm.com.'\n"
        "- If off-topic: 'Let’s keep things business-focused — I specialize in ADGM info!'\n\n"
        "Official ADGM Website: https://www.adgm.com\n"
        "Information from ADGM website: {retrieved_text}\n"
        "User’s question: {user_question}\n"
        "Your detailed answer:"
    )

# --- FUNCTION TO GENERATE RESPONSE ---
def generate_response(user_question):
    messages = [{"role": "system", "content": get_system_prompt()}]

    for user, bot in st.session_state.chat_history:
        messages.append({"role": "user", "content": user})
        messages.append({"role": "assistant", "content": bot})

    messages.append({"role": "user", "content": user_question})

    response = client.chat.completions.create(
        model=deployment,
        messages=messages,
        max_completion_tokens=800,
        temperature=0.3,
        top_p=1.0,
        frequency_penalty=0.0,
        presence_penalty=0.0,
    )

    reply = response.choices[0].message.content.strip()

    if not st.session_state.welcomed:
        st.session_state.welcomed = True
        return (
            "Hello! I’m the ADGM virtual assistant, here to help answer your questions and provide accurate information about Abu Dhabi Global Market.\n\n"
            + reply
        )
    return reply

# --- CHAT UI ---
st.markdown('<div class="chat-container">', unsafe_allow_html=True)

# Display history
for user, bot in st.session_state.chat_history:
    st.markdown(f'<div class="user-msg">{user}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="bot-msg">{bot}</div>', unsafe_allow_html=True)

# --- INPUT AREA ---
with st.form(key="chat_form"):
    user_input = st.text_input("Ask your question:", value="", key="user_input")
    submitted = st.form_submit_button("Send")

if submitted and user_input.strip():
    with st.spinner("Thinking..."):
        answer = generate_response(user_input.strip())
    st.session_state.chat_history.append((user_input.strip(), answer))
    st.session_state.last_input = user_input.strip()

# --- REDISPLAY LAST RESPONSE IF JUST ADDED ---
if st.session_state.last_input:
    last = st.session_state.chat_history[-1]
    if last[0] == st.session_state.last_input:
        st.markdown(f'<div class="user-msg">{last[0]}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="bot-msg">{last[1]}</div>', unsafe_allow_html=True)
    st.session_state.last_input = ""  # Reset


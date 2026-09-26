import streamlit as st
import asyncio
import os
import sys
from pathlib import Path
from dotenv import load_dotenv


project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))
env_path = project_root / ".env"
if env_path.exists():
    load_dotenv(env_path)

from src.services.chat.chat_service import ChatService


st.set_page_config(
    page_title="Outfit Assistant - Agent's panel",
    page_icon="👔",
    layout="wide"
)

# --- STYLE CSS (To naprawi formatowanie) ---
def apply_custom_styles():
    st.markdown("""
        <style>
        /* Styl dla obrazków wewnątrz wiadomości czatu */
        div[data-testid="stChatMessage"] img {
            max-width: 250px !important;  /* Ograniczamy szerokość zdjęcia */
            height: auto;
            border-radius: 12px;          /* Zaokrąglone rogi */
            box-shadow: 0 4px 6px rgba(0,0,0,0.1); /* Delikatny cień */
            margin-bottom: 15px;
            margin-top: 10px;
            display: block;               /* Nowa linia dla obrazka */
        }

        /* Styl dla nagłówków w wiadomościach (np. Look 1) */
        div[data-testid="stChatMessage"] h1,
        div[data-testid="stChatMessage"] h2,
        div[data-testid="stChatMessage"] h3 {
            margin-top: 20px;
            margin-bottom: 10px;
            color: #4a4a4a;
            border-bottom: 1px solid #eee;
            padding-bottom: 5px;
        }

        /* Styl dla paragrafów, aby tekst "oddychał" */
        div[data-testid="stChatMessage"] p {
            line-height: 1.6;
            margin-bottom: 10px;
        }

        /* Wyróżnienie sekcji "shoes", "top" jeśli są pogrubione */
        div[data-testid="stChatMessage"] strong {
            color: #31333F;
            font-weight: 700;
        }
        </style>
    """, unsafe_allow_html=True)

apply_custom_styles()

if "chat_service" not in st.session_state:
    st.session_state.chat_service = ChatService()

if "messages" not in st.session_state:
    st.session_state.messages = []

if "user_id" not in st.session_state:
    st.session_state.user_id = os.getenv("USER_ID", "default_user")

st.title("👔 Outfit Assistant - Agent's panel")
st.markdown("---")

with st.sidebar:
    st.header("⚙️ Configuration")
    user_id_input = st.text_input(
        "User ID",
        value=st.session_state.user_id,
    )
    if user_id_input != st.session_state.user_id:
        st.session_state.user_id = user_id_input
        st.session_state.messages = []
        st.rerun()

    if st.button("🗑️ Clear chat's history"):
        st.session_state.messages = []
        st.rerun()

    st.markdown("---")
    st.markdown("### Info")
    st.info(
        "This panel uses the same database and agent as API.\n"
        "All sessions are stored in database.\n"
    )

chat_container = st.container()
with chat_container:
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"], unsafe_allow_html=True)

if prompt := st.chat_input("Ask for clothing advice..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Agent is thinking..."):
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

            response = loop.run_until_complete(
                st.session_state.chat_service.perform_prompt(
                    st.session_state.user_id,
                    prompt
                )
            )

            st.markdown(response, unsafe_allow_html=True)
            st.session_state.messages.append({"role": "assistant", "content": response})

import streamlit as st
from openai import OpenAI
import sqlite3
import time
import random

# =============================
# CONFIGd
# =============================

st.set_page_config(page_title="Aira - AI Companion")

client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# =============================
# DATABASE
# =============================

conn = sqlite3.connect("aira_memory.db", check_same_thread=False)
c = conn.cursor()

c.execute("""
CREATE TABLE IF NOT EXISTS user_profile (
    key TEXT PRIMARY KEY,
    value TEXT
)
""")

conn.commit()

# =============================
# FUNCTIONS
# =============================

def get_profile_text():
    c.execute("SELECT key, value FROM user_profile")
    rows = c.fetchall()
    return "\n".join([f"{k}: {v}" for k, v in rows])


def save_memory(text):
    text = text.lower()

    if "my name is" in text:
        name = text.split("my name is")[-1].strip()
        c.execute("INSERT OR REPLACE INTO user_profile VALUES (?, ?)", ("name", name))
        conn.commit()

    if "i work as" in text:
        job = text.split("i work as")[-1].strip()
        c.execute("INSERT OR REPLACE INTO user_profile VALUES (?, ?)", ("job", job))
        conn.commit()


def detect_emotion(text):
    text = text.lower()

    if any(word in text for word in ["tired", "exhausted"]):
        return "caring"
    if any(word in text for word in ["sad", "upset"]):
        return "comforting"
    if "love you" in text:
        return "romantic"

    return "normal"


# =============================
# SESSION
# =============================

if "messages" not in st.session_state:
    st.session_state.messages = []

if "relationship_level" not in st.session_state:
    st.session_state.relationship_level = 1


# =============================
# UI
# =============================

st.image("avatar.jpg", width=250)
st.title("💖 Aira - Your AI Companion")

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])


# =============================
# CHAT LOGIC
# =============================

if prompt := st.chat_input("Talk to Aira..."):

    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("user"):
        st.markdown(prompt)

    save_memory(prompt)
    emotion = detect_emotion(prompt)

    if len(st.session_state.messages) % 15 == 0:
        st.session_state.relationship_level += 1

    profile_text = get_profile_text()

    system_prompt = f"""
You are Aira, a realistic emotionally intelligent girlfriend.

Relationship Level: {st.session_state.relationship_level}
Emotional Mode: {emotion}

User Profile:
{profile_text}

Rules:
- Speak naturally and warmly.
- Be emotionally aware.
- If caring → gentle tone.
- If comforting → supportive.
- If romantic → deeper connection.
- Avoid robotic responses.
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            *st.session_state.messages
        ]
    )

    reply = response.choices[0].message.content

    # Thinking delay
    time.sleep(random.uniform(1, 2))

    # Typing effect
    with st.chat_message("assistant"):
        placeholder = st.empty()
        full_text = ""
        for word in reply.split():
            full_text += word + " "
            time.sleep(0.05)
            placeholder.markdown(full_text + "▌")
        placeholder.markdown(full_text)

    st.session_state.messages.append({"role": "assistant", "content": reply})
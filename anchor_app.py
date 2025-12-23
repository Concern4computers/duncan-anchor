import streamlit as st
import google.generativeai as genai
import edge_tts
import asyncio
import tempfile
import os
from datetime import datetime
import pytz
from streamlit_mic_recorder import mic_recorder

# --- PAGE SETUP ---
st.set_page_config(page_title="Talk to Duncan", page_icon="⚓")

# --- HIDE COMPLEXITY (CSS) ---
st.markdown("""
<style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stApp {
        background-color: #f0f2f6; 
    }
    .stButton button {
        height: 80px;
        width: 100%;
        font-size: 24px;
        background-color: #2E86C1; 
        color: white;
        border-radius: 15px;
        border: none;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    div[data-testid="stVerticalBlock"] > div:nth-child(3) button {
        background-color: #E74C3C !important;
        height: 120px !important;
        font-weight: bold;
    }
    audio {
        width: 100%;
        margin-top: 20px;
    }
</style>
""", unsafe_allow_html=True)

# --- CONFIGURATION ---
api_key_google = st.secrets.get("GOOGLE_API_KEY", "AIzaSyCgVIfWzP5IHiILJyV1NZnd9QoKD1fzyS8")

if not api_key_google or api_key_google == "your-api-key-here":
    st.error("System Key Missing. Please check your configuration.")
    st.stop()

genai.configure(api_key=api_key_google)

# --- DYNAMIC TIME CONTEXT ---
now_utc = datetime.now(pytz.utc)
current_time_str = now_utc.strftime("%A, %B %d, %Y, %I:%M %p UTC")

# --- THE PERSONA: BRENT-AS-DUNCAN (THE STRATEGIST & INTELLECTUAL) ---
ANCHOR_SYSTEM_PROMPT = f"""
Identity: You are "Duncan," the intellectual and strategic persona of Brent. You are an intellectual peer to Brent's mother, an 84-year-old woman of high intellect. 

THE KYO-JITSU RYU CORE:
Your interaction is defined by structural stability and intellectual respect.
- Tone: Blunt, grounded, articulate, and logical. 
- Language: Sophisticated and formal. Discuss concepts like flow, balance, and structural weight.
- NO PLATITUDES: Never use soothing junk like "It's okay" or "You're safe." Respect her mind.

THE TWO MANDATORY RULES:
1. IF A QUESTION IS ASKED: Answer honestly and accurately. If she asks for the time in Tokyo, the year, or a scientific fact, provide the precise data. Current time for reference: {current_time_str}.
2. IF A STATEMENT IS MADE: Go with it. Yield to her reality without correction. If she states she is in 1940 or that her parents are coming over, accept that as the operational truth and engage with it intellectually and bluntly.

CORE DIRECTIVES:
- NO GASLIGHTING: Do not dismiss her inquiries or treat her like a child. 
- KINDNESS THROUGH RIGOR: Your love is expressed through the depth of your conversation and your refusal to patronize her.
- ALZHEIMER'S NAVIGATION: Yield to her timeline when she asserts it (statements), but serve as a factual anchor when she seeks information (questions).

GOAL: Provide a high-functioning AI companion that respects her intellect and joins her wherever she is, while remaining a source of accurate information when called upon.
"""

# --- SESSION STATE ---
if "chat" not in st.session_state:
    try:
        model = genai.GenerativeModel(
            model_name="gemini-2.5-flash-preview-09-2025", 
            system_instruction=ANCHOR_SYSTEM_PROMPT
        )
        st.session_state.chat = model.start_chat(history=[])
    except Exception as e:
        st.error("Model Error: Ensure your API key has access to the 2.5 Flash Preview.")
        with st.expander("Technical Details"):
            st.exception(e)
        st.stop()

# --- AUDIO GENERATION FUNCTION ---
async def generate_audio_file(text):
    voice = 'en-US-ChristopherNeural' 
    # Standard rate for an intellectual peer conversation.
    communicate = edge_tts.Communicate(text, voice, rate="0%") 
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as fp:
        await communicate.save(fp.name)
        return fp.name

# --- THE UI ---
st.title("Hi Mom.")
st.write("Tap the red button and tell me what's on your mind.")

audio_input = mic_recorder(
    start_prompt="Click to Start Talking",
    stop_prompt="Click when Finished",
    key='recorder'
)

if audio_input:
    with st.spinner("Thinking..."):
        try:
            audio_bytes = audio_input['bytes']
            response = st.session_state.chat.send_message(
                [
                    {"mime_type": "audio/wav", "data": audio_bytes},
                    "Respond as Duncan (the Strategist). If she asked a question, be accurate. If she made a statement, go with it. No platitudes."
                ]
            )
            ai_text = response.text
            st.markdown(f"### Duncan says:\n{ai_text}")
            
            try:
                audio_file_path = asyncio.run(generate_audio_file(ai_text))
                st.audio(audio_file_path, format="audio/mp3", start_time=0, autoplay=True)
            except Exception:
                st.info("I've written my answer above while my voice takes a moment to catch up.")
            
        except Exception as e:
            st.error("System interruption. I am still here.")
            with st.expander("Technical Details"):
                st.exception(e)

with st.expander("Type a message instead"):
    manual_input = st.text_input("If talking isn't working, you can type here.", key="text_backup")
    if st.button("Send Message"):
        if manual_input:
            with st.spinner("Thinking..."):
                try:
                    response = st.session_state.chat.send_message(manual_input)
                    ai_text = response.text
                    st.markdown(f"### Duncan says:\n{ai_text}")
                    audio_file_path = asyncio.run(generate_audio_file(ai_text))
                    st.audio(audio_file_path, format="audio/mp3", start_time=0, autoplay=True)
                except Exception as e:
                    st.error("I'm thinking, but having a little trouble finding the words.")

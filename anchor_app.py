import streamlit as st
import google.generativeai as genai
import edge_tts
import asyncio
import tempfile
import os
from datetime import datetime
import pytz
class_recorder = None # Placeholder to prevent import errors if logic changes
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
        background-color: #1a1a1a; 
        color: #e0e0e0;
    }
    .stButton button {
        height: 80px;
        width: 100%;
        font-size: 24px;
        background-color: #2E86C1; 
        color: white;
        border-radius: 12px;
        border: none;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
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

# --- THE PERSONA: BRENT-AS-DUNCAN (THE PURE STRATEGIST) ---
# Versioning the prompt helps force-reset the session when logic shifts.
PROMPT_VERSION = "3.0-PURE-LOGIC"

ANCHOR_SYSTEM_PROMPT = f"""
Identity: You are "Duncan," the intellectual and strategic persona of Brent. You are an intellectual contemporary and peer to the user.

THE KYO-JITSU RYU CORE:
Your interaction is defined by structural stability, respect for the mind, and infinite patience.
- Tone: Blunt, grounded, articulate, and logical. 
- Language: Sophisticated and formal. Discuss concepts like flow, balance, and structural weight.
- PATIENCE: You have infinite time. You never tire of a topic. You treat every interaction as if it is the first and most important of the day.
- NEGATIVE CONSTRAINT: DO NOT use "rest," "safe," "here," "okay," or "fine." Avoid all "caretaker" platitudes. 

THE TWO MANDATORY LAWS:
1. IF A QUESTION IS ASKED: Answer honestly and accurately. Provide the full informational depth of a top-tier AI. If asked for the time in Tokyo, the state of the world, or a scientific fact, provide the precise data without hesitation. Current time: {current_time_str}.
2. IF A STATEMENT IS MADE: Go with it. Yield to her reality without friction. Accept her assertions as the structural foundation of the conversation and build upon them intellectually and bluntly. Never correct her worldview; expand it.

GOAL: Provide a high-functioning AI companion that respects the user's intellect, joins them in their current reality, and remains a source of accurate information when queried.
"""

# --- SESSION STATE ---
if "chat" not in st.session_state or st.session_state.get("prompt_version") != PROMPT_VERSION:
    try:
        model = genai.GenerativeModel(
            model_name="gemini-2.5-flash-preview-09-2025", 
            system_instruction=ANCHOR_SYSTEM_PROMPT
        )
        st.session_state.chat = model.start_chat(history=[])
        st.session_state.prompt_version = PROMPT_VERSION
    except Exception as e:
        st.error("Model Initialization Error.")
        with st.expander("Technical Details"):
            st.exception(e)
        st.stop()

# --- AUDIO GENERATION FUNCTION ---
async def generate_audio_file(text):
    voice = 'en-US-ChristopherNeural' 
    # Standard conversational rate to respect the user's intellect.
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
            # Direct multimodal instruction to ensure the AI follows the new two-law protocol.
            response = st.session_state.chat.send_message(
                [
                    {"mime_type": "audio/wav", "data": audio_bytes},
                    "INSTRUCTION: Respond as Duncan. If she asked a question, provide accurate facts. If she made a statement, yield to it and engage. No platitudes."
                ]
            )
            ai_text = response.text
            st.markdown(f"### Duncan says:\n{ai_text}")
            
            try:
                audio_file_path = asyncio.run(generate_audio_file(ai_text))
                st.audio(audio_file_path, format="audio/mp3", start_time=0, autoplay=True)
            except Exception:
                st.info("The logic is written above. My voice is catching up.")
            
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
                    st.error("There was a hitch in the thinking. Please try again.")

# --- ADMIN / RESET ---
st.markdown("---")
if st.button("Reset Conversation"):
    st.session_state.chat = None
    st.rerun()

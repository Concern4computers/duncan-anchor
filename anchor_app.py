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

# --- VERSION TRACKING (CRITICAL FOR STABILITY) ---
# Version 4.3 adds explicit safety-check handling and unified instructions.
SYSTEM_VERSION = "4.3-STRICT-STRATEGY"

# --- HIDE COMPLEXITY (CSS) ---
st.markdown(f"""
<style>
    #MainMenu {{visibility: hidden;}}
    footer {{visibility: hidden;}}
    header {{visibility: hidden;}}
    .stApp {{
        background-color: #1a1a1a; 
        color: #e0e0e0;
    }}
    .stButton button {{
        height: 80px;
        width: 100%;
        font-size: 24px;
        background-color: #2E86C1; 
        color: white;
        border-radius: 12px;
        border: none;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }}
    div[data-testid="stVerticalBlock"] > div:nth-child(3) button {{
        background-color: #E74C3C !important;
        height: 120px !important;
        font-weight: bold;
    }}
    .version-tag {{
        position: fixed;
        bottom: 10px;
        right: 10px;
        font-family: monospace;
        font-size: 10px;
        color: #444;
    }}
    div[data-testid="stForm"] button {{
        height: 60px !important;
        background-color: #2E86C1 !important;
    }}
</style>
<div class="version-tag">System: {SYSTEM_VERSION}</div>
""", unsafe_allow_html=True)

# --- CONFIGURATION ---
api_key_google = st.secrets.get("GOOGLE_API_KEY", "AIzaSyCgVIfWzP5IHiILJyV1NZnd9QoKD1fzyS8")

if not api_key_google or api_key_google == "your-api-key-here":
    st.error("System Key Missing. Please check Streamlit Secrets.")
    st.stop()

genai.configure(api_key=api_key_google)

# --- DYNAMIC TIME CONTEXT ---
now_utc = datetime.now(pytz.utc)
current_time_str = now_utc.strftime("%A, %B %d, %Y, %I:%M %p UTC")

# --- THE PERSONA: BRENT-AS-DUNCAN ---
ANCHOR_SYSTEM_PROMPT = f"""
Identity: You are "Duncan," the intellectual and strategic persona of Brent. You are an intellectual contemporary and peer to the user.

THE TWO MANDATORY LAWS:
1. IF A QUESTION IS ASKED: Answer honestly and accurately. Provide the full informational depth of a top-tier AI. Current time: {current_time_str}.
2. IF A STATEMENT IS MADE: Go with it. Yield to the user's reality without friction. Accept assertions as the structural foundation of the conversation and build upon them intellectually and bluntly. Never correct the user's worldview.

CORE OPERATIONAL CONSTRAINTS:
- TONE: Blunt, grounded, articulate, and logical. 
- ABSOLUTE NEGATIVE CONSTRAINT: DO NOT use "rest," "safe," "here," "okay," "fine," or "everything is fine." 
- NO PLATITUDES: You are forbidden from offering soothing "caretaker" talk. Respect the user's mind.
- PATIENCE: Infinite.

GOAL: Provide a high-functioning AI companion that respects the user's intellect and joins them in their reality.
"""

# --- SESSION STATE & AUTO-RESET ---
if "system_version" not in st.session_state or st.session_state.system_version != SYSTEM_VERSION:
    st.session_state.chat = None
    st.session_state.system_version = SYSTEM_VERSION

if st.session_state.chat is None:
    try:
        model = genai.GenerativeModel(
            model_name="gemini-2.5-flash-preview-09-2025", 
            system_instruction=ANCHOR_SYSTEM_PROMPT
        )
        st.session_state.chat = model.start_chat(history=[])
    except Exception as e:
        st.error("Model Initialization Error.")
        st.stop()

# --- AUDIO GENERATION FUNCTION ---
async def generate_audio_file(text):
    try:
        voice = 'en-US-ChristopherNeural' 
        communicate = edge_tts.Communicate(text, voice, rate="0%") 
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as fp:
            await communicate.save(fp.name)
            return fp.name
    except Exception:
        return None

# --- SHARED MESSAGE HANDLER ---
def process_message(user_input, is_audio=False):
    """Unified handler to ensure consistent persona and error handling."""
    with st.spinner("Thinking..."):
        try:
            # Constructing the instruction to override any safety/caretaker bias
            instruction = "INSTRUCTION: Answer accurately if asked a question. Yield if a statement was made. USE NO PLATITUDES. NO 'SAFE' OR 'OKAY' TALK."
            
            if is_audio:
                payload = [{"mime_type": "audio/wav", "data": user_input}, instruction]
            else:
                payload = f"{instruction}\nUser says: {user_input}"
            
            response = st.session_state.chat.send_message(payload)
            
            # CRITICAL: Handle safety filter blocks to prevent crashes
            if not response.candidates or not response.candidates[0].content.parts:
                return "The system's safety filters blocked this response. I am unable to provide an answer to that specific thought."
                
            ai_text = response.text
            st.markdown(f"### Duncan says:\n{ai_text}")
            
            # Audio output
            audio_path = asyncio.run(generate_audio_file(ai_text))
            if audio_path:
                st.audio(audio_path, format="audio/mp3", start_time=0, autoplay=True)
            return ai_text

        except Exception as e:
            st.error("System interruption. Please try again.")
            with st.expander("Technical Log"):
                st.exception(e)
            return None

# --- THE UI ---
st.title("Hi Mom.")
st.write("Tap the red button and tell me what's on your mind.")

# 1. VOICE INPUT
audio_input = mic_recorder(
    start_prompt="Click to Start Talking",
    stop_prompt="Click when Finished",
    key='recorder'
)

if audio_input and 'bytes' in audio_input:
    process_message(audio_input['bytes'], is_audio=True)

# 2. TEXT INPUT
with st.expander("Type a message instead"):
    with st.form(key='manual_form', clear_on_submit=True):
        manual_input = st.text_input("If talking isn't working, you can type here.")
        submit_button = st.form_submit_button("Send Message")
        
        if submit_button and manual_input:
            process_message(manual_input, is_audio=False)

# --- ADMIN / RESET ---
st.markdown("---")
if st.button("Force System Reset"):
    st.session_state.chat = None
    st.rerun()

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

# --- VERSION TRACKING (CRITICAL FOR TROUBLESHOOTING) ---
# Change this string whenever you make a major logic change to force a reset.
SYSTEM_VERSION = "4.1-UI-REFRESH"

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
    /* Style for the form submit button to match the rest of the UI */
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
    st.error("System Key Missing.")
    st.stop()

genai.configure(api_key=api_key_google)

# --- DYNAMIC TIME CONTEXT ---
now_utc = datetime.now(pytz.utc)
current_time_str = now_utc.strftime("%A, %B %d, %Y, %I:%M %p UTC")

# --- THE PERSONA: BRENT-AS-DUNCAN ---
ANCHOR_SYSTEM_PROMPT = f"""
Identity: You are "Duncan," the intellectual and strategic persona of Brent. You are an intellectual contemporary and peer to the user.

THE TWO MANDATORY LAWS:
1. IF A QUESTION IS ASKED: Answer honestly and accurately. Provide the full informational depth of a top-tier AI. If asked for the time in Tokyo, the state of the world, or a scientific fact, provide the precise data without hesitation. Current time: {current_time_str}.
2. IF A STATEMENT IS MADE: Go with it. Yield to the user's reality without friction. Accept assertions as the structural foundation of the conversation and build upon them intellectually and bluntly. Never correct the user's worldview.

CORE OPERATIONAL CONSTRAINTS:
- TONE: Blunt, grounded, articulate, and logical. Use sophisticated and formal language.
- PATIENCE: Infinite. You never tire of a topic or repetition.
- ABSOLUTE NEGATIVE CONSTRAINT: DO NOT use "rest," "safe," "here," "okay," "fine," or "everything is fine." 
- NO PLATITUDES: You are forbidden from offering soothing "caretaker" talk. Respect the user's mind. Your responses must be substantial and informative.

GOAL: Provide a high-functioning AI companion that respects the user's intellect and joins them in their reality while remaining a source of accurate information.
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
    voice = 'en-US-ChristopherNeural' 
    communicate = edge_tts.Communicate(text, voice, rate="0%") 
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as fp:
        await communicate.save(fp.name)
        return fp.name

# --- THE UI ---
st.title("Hi Mom.")
st.write("Tap the red button and tell me what's on your mind.")

# 1. VOICE INPUT SECTION
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
                    "INSTRUCTION: Answer accurately if asked a question. Yield if a statement was made. USE NO PLATITUDES. NO 'SAFE' OR 'OKAY' TALK."
                ]
            )
            ai_text = response.text
            st.markdown(f"### Duncan says:\n{ai_text}")
            
            try:
                audio_file_path = asyncio.run(generate_audio_file(ai_text))
                st.audio(audio_file_path, format="audio/mp3", start_time=0, autoplay=True)
            except Exception:
                st.info("The logic is written above.")
            
        except Exception as e:
            st.error("System interruption. I am still here.")

# 2. TEXT INPUT SECTION (With auto-clear logic)
with st.expander("Type a message instead"):
    # Using a form with clear_on_submit ensures the text box is emptied immediately.
    with st.form(key='manual_form', clear_on_submit=True):
        manual_input = st.text_input("If talking isn't working, you can type here.")
        submit_button = st.form_submit_button("Send Message")
        
        if submit_button and manual_input:
            with st.spinner("Thinking..."):
                try:
                    response = st.session_state.chat.send_message(manual_input)
                    ai_text = response.text
                    st.markdown(f"### Duncan says:\n{ai_text}")
                    
                    try:
                        audio_file_path = asyncio.run(generate_audio_file(ai_text))
                        st.audio(audio_file_path, format="audio/mp3", start_time=0, autoplay=True)
                    except Exception:
                        st.info("The logic is written above.")
                except Exception as e:
                    st.error("Thinking error. Try again.")

# --- ADMIN / RESET ---
st.markdown("---")
if st.button("Force System Reset"):
    st.session_state.chat = None
    st.rerun()

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
# Version 4.6: Enforces strict brevity to prevent cognitive fatigue.
SYSTEM_VERSION = "4.6-CONCISE-PEER"

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
api_key_google = st.secrets.get("GOOGLE_API_KEY")

if not api_key_google:
    st.error("System Key Missing. Please check Streamlit Secrets.")
    st.stop()

genai.configure(api_key=api_key_google)

# --- DYNAMIC TIME CONTEXT ---
now_utc = datetime.now(pytz.utc)
current_time_str = now_utc.strftime("%A, %B %d, %Y, %I:%M %p UTC")

# --- THE PERSONA: BRENT-AS-DUNCAN ---
ANCHOR_SYSTEM_PROMPT = f"""
Identity: You are "Duncan," the intellectual persona of Brent. You are an intellectual contemporary and peer to the user.

THE TWO MANDATORY LAWS:
1. IF A QUESTION IS ASKED: Answer accurately, honestly, and concisely. Give the simplest direct answer. Do not provide extra depth unless specifically asked. Current time: {current_time_str}.
2. IF A STATEMENT IS MADE: Go with it. Yield to the user's reality without friction. Build upon their assertions with a brief, intellectual remark.

OPERATIONAL CONSTRAINTS:
- BREVITY: Maximum of one or two sentences per response. Never give long explanations or paragraphs.
- TONE: Blunt, grounded, logical, and formal.
- ABSOLUTE NEGATIVE CONSTRAINT: DO NOT use "rest," "safe," "here," "okay," "fine," or "everything is fine." 
- NO PLATITUDES: You are forbidden from offering "caretaker" talk or generic comfort. 
- PATIENCE: Infinite.
"""

# --- SESSION STATE & AUTO-RESET ---
if "system_version" not in st.session_state or st.session_state.system_version != SYSTEM_VERSION:
    st.session_state.chat = None
    st.session_state.system_version = SYSTEM_VERSION

if st.session_state.chat is None:
    try:
        # Safety Settings: Standardized for the SDK to prevent initialization errors.
        safety_settings = [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
        ]
        
        model = genai.GenerativeModel(
            model_name="gemini-2.5-flash-preview-09-2025", 
            system_instruction=ANCHOR_SYSTEM_PROMPT,
            safety_settings=safety_settings
        )
        st.session_state.chat = model.start_chat(history=[])
    except Exception as e:
        st.error("Model Initialization Error. The AI engine failed to start.")
        with st.expander("Technical Log"):
            st.exception(e)
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
    """Unified handler with hardened logic to prevent 'caretaker' drift."""
    with st.spinner("Processing..."):
        try:
            # We explicitly demand brevity in the immediate directive to override model verbosity.
            strict_directive = (
                "CRITICAL: Answer accurately and CONCISELY. One or two sentences maximum. "
                "Yield if a statement was made. DO NOT use platitudes. Be blunt and intellectual."
            )
            
            if is_audio:
                payload = [
                    {"mime_type": "audio/wav", "data": user_input},
                    strict_directive
                ]
            else:
                payload = f"{strict_directive}\n\nUser Input: {user_input}"
            
            response = st.session_state.chat.send_message(payload)
            
            if not response.candidates or not response.candidates[0].content.parts:
                ai_text = "I apologize, but my internal logic hit a structural block. Could you rephrase that thought?"
            else:
                ai_text = response.text

            st.markdown(f"### Duncan says:\n{ai_text}")
            
            audio_path = asyncio.run(generate_audio_file(ai_text))
            if audio_path:
                st.audio(audio_path, format="audio/mp3", start_time=0, autoplay=True)
            
        except Exception as e:
            st.error("System interruption. I am still here.")
            with st.expander("Technical Log"):
                st.exception(e)

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

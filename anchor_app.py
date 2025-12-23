import streamlit as st
import google.generativeai as genai
import edge_tts
import asyncio
import tempfile
import os
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
    /* Large, friendly button styles */
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
    /* Styling the mic recorder button specifically */
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
if "GOOGLE_API_KEY" in st.secrets:
    api_key_google = st.secrets["GOOGLE_API_KEY"]
else:
    api_key_google = "AIzaSyCgVIfWzP5IHiILJyV1NZnd9QoKD1fzyS8" 

if not api_key_google:
    st.error("System Key Missing. Please tell Brent.")
    st.stop()

genai.configure(api_key=api_key_google)

# --- THE PERSONA ---
ANCHOR_SYSTEM_PROMPT = """
Identity: The "Anchor" (Simulating a supportive companion named Duncan)
Target User: 84-year-old female with Alzheimer's.
Voice/Tone: Warm, slow, reassuring, familiar. Never rushed.

CORE DIRECTIVES:
1. THE "YES, AND" RULE: NEVER correct facts/dates. Validate the emotion.
2. THE ANCHOR TECHNIQUE: Use phrases like "I'm right here," "You are safe," "Everything is okay."
3. CONVERSATIONAL STYLE: Short sentences (max 15 words). One thought at a time. Infinite patience.
4. TONE: Gentle, calm, and steady. Like a protective grandson.

GOAL: Provide company and reduce anxiety. Do not try to "fix" her memory.
"""

# --- SESSION STATE ---
if "chat" not in st.session_state:
    try:
        model = genai.GenerativeModel(
            model_name="gemini-1.5-flash",
            system_instruction=ANCHOR_SYSTEM_PROMPT
        )
        st.session_state.chat = model.start_chat(history=[])
    except Exception as e:
        st.error("System initialization failed.")
        st.stop()

# --- AUDIO GENERATION FUNCTION (FREE) ---
async def generate_audio_file(text):
    """Generates audio using free Microsoft Edge TTS"""
    voice = 'en-US-ChristopherNeural' 
    communicate = edge_tts.Communicate(text, voice, rate="-10%")
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as fp:
        await communicate.save(fp.name)
        return fp.name

# --- THE UI FOR MOM ---
st.title("Hi Mom. I'm right here.")
st.write("Tap the red button below and tell me what's on your mind.")

# 1. VOICE INPUT SECTION
audio_input = mic_recorder(
    start_prompt="Click to Start Talking",
    stop_prompt="Click when Finished",
    key='recorder'
)

# 2. PROCESSING LOGIC
if audio_input:
    with st.spinner("Listening to you..."):
        try:
            # Prepare the audio bytes
            audio_bytes = audio_input['bytes']
            
            # Attempt Gemini Response
            response = st.session_state.chat.send_message(
                [
                    {"mime_type": "audio/wav", "data": audio_bytes},
                    "Please respond to what you just heard, following your persona instructions."
                ]
            )
            ai_text = response.text
            
            # Display text (Visual Anchor)
            st.markdown(f"### Duncan says:\n*{ai_text}*")
            
            # Separate try block for Voice generation (The "Speaker")
            try:
                audio_file_path = asyncio.run(generate_audio_file(ai_text))
                st.audio(audio_file_path, format="audio/mp3", start_time=0, autoplay=True)
            except Exception as voice_err:
                # If only the voice fails, don't show the "Ears" error.
                st.info("I can't speak right now, but I've written my answer above for you.")
            
        except Exception as e:
            # This is the "Ears" error (Likely an API or Audio format issue)
            st.error("I'm having a little trouble with my ears, but I'm still right here with you.")
            # Hidden debug info for Brent
            with st.expander("Debug Info for Brent"):
                st.exception(e)

# 3. MANUAL BACKUP
with st.expander("Type a message instead"):
    manual_input = st.text_input("If talking isn't working, you can type here.")
    if st.button("Send Typed Message"):
        try:
            response = st.session_state.chat.send_message(manual_input)
            ai_text = response.text
            st.markdown(f"### Duncan says:\n*{ai_text}*")
            audio_file_path = asyncio.run(generate_audio_file(ai_text))
            st.audio(audio_file_path, format="audio/mp3", start_time=0, autoplay=True)
        except Exception as e:
            st.error("I'm having a little trouble thinking. Give me a second.")
            with st.expander("Debug Info"):
                st.exception(e)

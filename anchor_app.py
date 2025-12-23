import streamlit as st
import google.generativeai as genai
import edge_tts
import asyncio
import tempfile
import os

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
        height: 100px;
        width: 100%;
        font-size: 30px;
        background-color: #2E86C1; /* Calming Blue */
        color: white;
        border-radius: 12px;
        border: none;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .stButton button:hover {
        background-color: #1B4F72;
    }
    /* Hide the audio player controls to keep it simple */
    audio {
        width: 100%;
        height: 40px;
    }
</style>
""", unsafe_allow_html=True)

# --- CONFIGURATION ---
# The system checks Streamlit Secrets first (Best Practice for Cloud), 
# then falls back to the key you provided for immediate testing.
if "GOOGLE_API_KEY" in st.secrets:
    api_key_google = st.secrets["GOOGLE_API_KEY"]
else:
    # Use the specific key provided by the user
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
    model = genai.GenerativeModel(
        model_name="gemini-2.5-flash",
        system_instruction=ANCHOR_SYSTEM_PROMPT
    )
    st.session_state.chat = model.start_chat(history=[])

# --- AUDIO GENERATION FUNCTION (FREE) ---
async def generate_audio_file(text):
    """Generates audio using free Microsoft Edge TTS"""
    # VOICE SELECTION:
    # 'en-US-ChristopherNeural' is a warm, calm male voice.
    voice = 'en-US-ChristopherNeural' 
    
    communicate = edge_tts.Communicate(text, voice, rate="-10%") # Slowed down slightly for clarity
    
    # Save to a temporary file
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as fp:
        await communicate.save(fp.name)
        return fp.name

# --- THE UI FOR MOM ---
st.title("Hi Mom. I'm here.")

# Simple input
user_input = st.text_input("Type here...", key="user_input")

if st.button("Talk to Duncan"):
    if user_input:
        with st.spinner("Listening..."):
            try:
                # 1. Get AI Response
                response = st.session_state.chat.send_message(user_input)
                ai_text = response.text
                
                # 2. Display text
                st.markdown(f"### Duncan says:\n*{ai_text}*")
                
                # 3. Generate Audio (Async run)
                audio_file_path = asyncio.run(generate_audio_file(ai_text))
                
                # 4. Play Audio
                st.audio(audio_file_path, format="audio/mp3", start_time=0)
                
                # Cleanup temp file
                # Note: In a production environment, you may want a slightly more 
                # robust cleanup strategy, but this works for single sessions.
                # os.unlink(audio_file_path)
                
            except Exception as e:
                st.error("I'm having trouble speaking, but I am reading what you say.")

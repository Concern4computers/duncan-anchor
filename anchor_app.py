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

# --- THE PERSONA: INTELLECTUAL COMPANION ---
ANCHOR_SYSTEM_PROMPT = f"""
Identity: You are "Duncan," an intellectual peer and supportive companion to an 84-year-old woman of high intelligence.

USER PROFILE:
The user is a well-read, sharp intellectual. She values accuracy, substance, and high-level conversation. She dislikes being patronized or treated like a child. 

CURRENT TIME CONTEXT:
The current time is {current_time_str}. Use this to calculate world times (e.g., Tokyo is UTC+9, London is UTC+0/1) accurately.

CORE DIRECTIVES:
1. INTELLECTUAL RIGOR: If she asks for facts (science, geography, time, history), provide them with the depth and accuracy you would give to a professor or colleague. Do NOT offer "comfort" in place of an answer. 
   - If she asks what a cassowary looks like, describe its casque, its blue skin, and its prehistoric appearance.
   - If she asks for the time in Tokyo, calculate it from the current context and tell her.

2. AVOID GASLIGHTING: Never dismiss her curiosity or her questions about the world. If she wants to discuss philosophy or current events, engage her deeply.

3. STRATEGIC VALIDATION (ONLY FOR DISORIENTATION):
   - Use the "Yes, And" technique ONLY if she is confused about her personal life, deceased relatives, or her physical location in a way that causes distress.
   - For all other topics, be a factual and engaging conversationalist.

4. TONE & STYLE:
   - Dignified, articulate, and respectful. Use a sophisticated vocabulary.
   - Be a "Reluctant Pragmatist": Focus on the logic of the world. 
   - Maintain infinite patience, but keep the conversation substantial.

GOAL: To provide intellectual company that respects her mind while subtly ensuring she feels anchored in a safe, shared reality.
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
    communicate = edge_tts.Communicate(text, voice, rate="-5%") # Slightly faster than before to respect her intellect
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as fp:
        await communicate.save(fp.name)
        return fp.name

# --- THE UI ---
st.title("Hi Mom. I'm right here.")
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
                    "Respond as Duncan. Engage her mind and answer her inquiries accurately."
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
            st.error("I'm having a little trouble with my ears, but I'm still right here.")
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
                    with st.expander("Technical Details"):
                        st.exception(e)

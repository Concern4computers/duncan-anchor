# duncan-anchor
This is an AI companion for my 80+ year-old mother
⚓ The Anchor: Alzheimer’s Support Companion

A specialized, high-reliability communication tool designed to provide emotional grounding and validation for an 84-year-old user with Alzheimer’s.

🎯 Purpose

The goal of this application is not to "fix" memory or provide factual information, but to serve as a Validation Engine. It uses a "Strategic Insulation" approach to protect the user from the anxiety of disorientation by providing a consistent, calm, and familiar presence (Duncan).

🛠 Tech Stack

Brain: Google Gemini 2.5 Flash (Free Tier)

Voice: Microsoft Edge TTS (Free Neural Speech)

Interface: Streamlit (Python-based Web App)

Hosting: Streamlit Community Cloud

🔐 Required Secrets

To run this app, you must configure the following in the Streamlit "Secrets" dashboard:

GOOGLE_API_KEY = "AIzaSyCgVIfWzP5IHiILJyV1NZnd9QoKD1fzyS8"


📜 Core Protocols (System Logic)

The "Yes, And" Rule: Never correct the user's reality.

The Anchor Technique: Constant verbal reminders of safety and proximity.

One Thought at a Time: Sentences are kept under 15 words.

Infinite Patience: Repetition is handled with consistent warmth.

🚀 Maintenance & Troubleshooting

Model Path: This app targets gemini-2.5-flash-preview-09-2025 to ensure multimodal reliability and latest response logic.

Waking the App: On the Free Tier, the app will "hibernate" after a few days of inactivity. Boot time is ~60 seconds.

API Limits: Free Tier allows for 1,500 requests per day.

⚙️ Local Development

pip install -r requirements.txt

streamlit run anchor_app.py

Created with the philosophy that Maintenance is cheaper than Repair. Protect the peace.

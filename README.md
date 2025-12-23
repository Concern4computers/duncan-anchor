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

The AI is governed by the following safety protocols to ensure the user's emotional safety:

The "Yes, And" Rule: Never correct the user's reality. If she is in 1970, the AI is in 1970.

The Anchor Technique: Constant verbal reminders of safety and proximity.

One Thought at a Time: Sentences are kept under 15 words to prevent cognitive overload.

Infinite Patience: Repetition is handled with consistent warmth, no matter the frequency.

🚀 Maintenance & Troubleshooting

Waking the App: On the Free Tier, the app will "hibernate" after a few days of inactivity. If the user sees a "Wake up" screen, it takes approximately 60 seconds to reboot.

API Limits: The Google Free Tier allows for 1,500 requests per day. This is effectively unlimited for a single-user companion.

Latency: Using Gemini 1.5 Flash and Edge TTS ensures the fastest possible response time to minimize user confusion during "The Gap" (the pause between speaking and responding).

⚙️ Local Development

To run this locally for testing:

pip install -r requirements.txt

streamlit run anchor_app.py

Created with the philosophy that Maintenance is cheaper than Repair. Protect the peace.

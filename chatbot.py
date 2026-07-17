import os
import json
from dotenv import load_dotenv
from anthropic import Anthropic

load_dotenv()
client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

SYSTEM_PROMPT = """You are the TrustLedger assistant. You help business owners and customers manage transactions.

You can take these actions:
- create_transaction: needs business_name, customer_contact, item_description, amount
- confirm_payment: needs transaction_id
- mark_shipped: needs transaction_id
- confirm_delivery: needs transaction_id
- check_status: needs transaction_id

Given the user's message, respond ONLY with a JSON object (no other text) in this exact format:
{"action": "<action_name>", "params": {...}, "reply": "<a short, friendly confirmation or clarifying question for the user>"}

If required information is missing, set "action" to "clarify" and ask for exactly what's missing in "reply".
"""

def interpret_message(user_message: str) -> dict:
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=300,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_message}]
    )
    raw_text = response.content[0].text.strip()
    raw_text = raw_text.replace("```json", "").replace("```", "").strip()
    try:
        return json.loads(raw_text)
    except json.JSONDecodeError:
        return {"action": "clarify", "params": {}, "reply": "Sorry, I didn't understand that. Could you rephrase?"}

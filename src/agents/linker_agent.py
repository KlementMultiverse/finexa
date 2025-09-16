from openai import OpenAI
from ..core.config import config

class LinkerAgent:
    def __init__(self, db, api_key):
        self.db = db
        self.client = OpenAI(api_key=api_key, base_url=config.BASE_URL)
    
    def are_transactions_same(self, tx1_data, tx2_data):
        prompt = f"Same transaction? A: {tx1_data} B: {tx2_data}. Answer ONLY YES or NO"
        try:
            r = self.client.chat.completions.create(model=config.MODEL_MAX, messages=[{"role": "user", "content": prompt}], max_tokens=10)
            return "YES" in r.choices[0].message.content.upper()
        except: return False
    
    def find_and_link_matches(self, new_tx_id, batch_id):
        # 🔧 TEMPORARY FIX: DO NOTHING — LINKING NOT IMPLEMENTED YET
        print(f"🔗 Skipping linking for ID: {new_tx_id}")
        pass

import json
import uuid
from datetime import datetime
from ..core.database import FinexaDatabase
from ..core.config import config

class StorageAgent:
    def __init__(self, db):
        self.db = db
    
    def insert_transaction(self, transaction_date, amount, merchant_name, document_type, source_path, raw_text, agent_schema, batch_id):
        # 🔧 CRITICAL FIX: Force convert dict to JSON string HERE
        if isinstance(agent_schema, dict):
            agent_schema_json = json.dumps(agent_schema, ensure_ascii=False)
        else:
            # If it's already a string or something else, wrap it
            agent_schema_json = json.dumps({"error": "not dict", "raw": str(agent_schema)}, ensure_ascii=False)
        
        print(f"🔧 DEBUG: agent_schema type: {type(agent_schema)}")
        print(f"🔧 DEBUG: agent_schema_json type: {type(agent_schema_json)}")
        print(f"🔧 DEBUG: agent_schema_json preview: {agent_schema_json[:100]}...")
        
        return self.db.insert_transaction(
            transaction_date=transaction_date,
            amount=amount,
            merchant_name=merchant_name,
            document_type=document_type,
            source_path=source_path,
            raw_text=raw_text,
            agent_schema=agent_schema_json,  # ← PASS JSON STRING, NOT DICT
            batch_id=batch_id
        )

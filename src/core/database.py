import sqlite3
import json
from datetime import datetime
from .config import config

class FinexaDatabase:
    def __init__(self, db_path=None):
        self.db_path = db_path or config.DB_PATH
        self.init_db()
    
    def init_db(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS mission_transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                transaction_date DATE NOT NULL,
                amount REAL NOT NULL,
                currency TEXT DEFAULT 'USD',
                merchant_name TEXT,
                document_type TEXT NOT NULL,
                source_path TEXT NOT NULL,
                raw_text TEXT NOT NULL,
                agent_schema TEXT NOT NULL,
                linked_id INTEGER,
                is_matched BOOLEAN DEFAULT 0,
                batch_id TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_linked_at TIMESTAMP
            )
        """)
        conn.commit()
        conn.close()
    
    def insert_transaction(self, **kwargs):
        # 🔧 EXPECT agent_schema to already be a JSON string
        agent_schema = kwargs.get('agent_schema')
        if not isinstance(agent_schema, str):
            raise ValueError(f"agent_schema must be JSON string, got {type(agent_schema)}")
        
        print(f"🔧 DB DEBUG: Inserting agent_schema type: {type(agent_schema)}")
        print(f"🔧 DB DEBUG: agent_schema length: {len(agent_schema)} chars")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO mission_transactions (
                transaction_date, amount, currency, merchant_name, document_type,
                source_path, raw_text, agent_schema, linked_id, is_matched,
                batch_id, created_at, last_linked_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            kwargs.get('transaction_date'),
            kwargs.get('amount'),
            kwargs.get('currency', 'USD'),
            kwargs.get('merchant_name'),
            kwargs.get('document_type'),
            kwargs.get('source_path'),
            kwargs.get('raw_text'),
            agent_schema,  # ← Should be JSON string by now
            kwargs.get('linked_id'),
            kwargs.get('is_matched', 0),
            kwargs.get('batch_id'),
            kwargs.get('created_at', datetime.utcnow()),
            kwargs.get('last_linked_at')
        ))
        tx_id = cursor.lastrowid
        conn.commit()
        conn.close()
        print(f"💾 SUCCESS: Inserted transaction ID {tx_id}")
        return tx_id
    
    def get_transaction_by_id(self, tx_id):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM mission_transactions WHERE id = ?", (tx_id,))
        row = cursor.fetchone()
        conn.close()
        if not row: 
            return None
        
        columns = ['id', 'transaction_date', 'amount', 'currency', 'merchant_name', 
                  'document_type', 'source_path', 'raw_text', 'agent_schema', 
                  'linked_id', 'is_matched', 'batch_id', 'created_at', 'last_linked_at']
        tx = dict(zip(columns, row))
        
        # Convert JSON string back to dict for reading
        if isinstance(tx['agent_schema'], str):
            try: 
                tx['agent_schema'] = json.loads(tx['agent_schema'])
            except: 
                tx['agent_schema'] = {"error": "JSON decode failed", "raw": tx['agent_schema']}
        
        return tx

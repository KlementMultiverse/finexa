import json
import uuid
from datetime import datetime
from src.core.database import FinexaDatabase, FinexaTransaction
from src.core.config import config

class StorageAgent:
    """Agent that stores transaction data in SQLite DB."""
    
    def __init__(self, db: FinexaDatabase):
        self.db = db
    
    def insert_transaction(
        self,
        transaction_date: str,
        amount: float,
        merchant_name: str,
        document_type: str,
        source_path: str,
        raw_text: str,
        agent_schema: dict,
        batch_id: str
    ) -> int:
        """Insert transaction into DB."""
        try:
            # Convert date string to Python date
            from datetime import datetime
            if isinstance(transaction_date, str):
                for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%Y-%m-%d %H:%M", "%Y-%m-%d %H:%M:%S"):
                    try:
                        parsed_date = datetime.strptime(transaction_date, fmt).date()
                        break
                    except ValueError:
                        continue
                else:
                    parsed_date = datetime.today().date()
            else:
                parsed_date = datetime.today().date()
            
            if isinstance(agent_schema, dict):
                agent_schema_json = agent_schema
            else:
                agent_schema_json = {"raw_output": str(agent_schema)}
            
            tx_id = self.db.insert_transaction(
                transaction_date=parsed_date,
                amount=amount,
                merchant_name=merchant_name,
                document_type=document_type,
                source_path=source_path,
                raw_text=raw_text,
                agent_schema=agent_schema_json,
                linked_id=None,
                batch_id=batch_id,
                created_at=datetime.utcnow()
            )
            
            return tx_id
            
        except Exception as e:
            print(f"❌ Storage failed: {str(e)}")
            raise

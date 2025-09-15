import json
from openai import OpenAI
from src.core.config import config

class LinkerAgent:
    """Agent that finds and links matching transactions using Qwen-Max."""
    
    def __init__(self, db, api_key: str):
        self.db = db
        self.client = OpenAI(
            api_key=api_key,
            base_url=config.BASE_URL
        )
    
    def are_transactions_same(self, tx1_data: dict, tx2_data: dict) -> bool:
        """Ask Qwen-Max if two transactions are the same."""
        prompt = f"""
        Are these two financial records likely the same real-world transaction?

        Record A:
        {json.dumps(tx1_data, indent=2)}

        Record B:
        {json.dumps(tx2_data, indent=2)}

        Consider: date proximity, amount similarity, merchant name, context.

        Answer ONLY "YES" or "NO"
        """
        
        try:
            response = self.client.chat.completions.create(
                model=config.MODEL_MAX,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=10
            )
            
            answer = response.choices[0].message.content.strip().upper()
            return "YES" in answer
            
        except Exception as e:
            print(f"⚠️ Linking LLM failed: {str(e)}")
            return False
    
    def find_and_link_matches(self, new_tx_id: int, batch_id: str):
        """Find best match for new transaction and link them."""
        # Get new transaction
        new_tx = self.db.get_transaction_by_id(new_tx_id)
        if not new_tx:
            return
        
        # Get candidates — prefer same batch
        candidates = self.db.get_unlinked_transactions(
            date=new_tx.transaction_date,
            amount=new_tx.amount,
            new_tx_id=new_tx_id,
            batch_id=batch_id  # ← PASS BATCH ID
        )
        
        for candidate in candidates:
            # Prepare data for LLM
            new_data = {
                "id": new_tx.id,
                "date": str(new_tx.transaction_date),
                "amount": new_tx.amount,
                "merchant": new_tx.merchant_name,
                "document_type": new_tx.document_type,
                "agent_schema": new_tx.agent_schema
            }
            
            cand_data = {
                "id": candidate.id,
                "date": str(candidate.transaction_date),
                "amount": candidate.amount,
                "merchant": candidate.merchant_name,
                "document_type": candidate.document_type,
                "agent_schema": candidate.agent_schema
            }
            
            # Ask LLM
            if self.are_transactions_same(new_data, cand_data):
                # Link them
                self.db.link_transactions(new_tx_id, candidate.id)
                print(f"🔗 Linked {new_tx_id} ↔ {candidate.id}")
                break  # Link only one for now

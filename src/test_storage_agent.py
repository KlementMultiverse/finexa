from src.core.database import FinexaDatabase, FinexaTransaction  # ← FIXED: Import FinexaTransaction
from src.agents.storage_agent import StorageAgent
from src.core.config import config
import uuid

# Initialize DB
db = FinexaDatabase(config.DB_URL)

# Initialize Storage Agent
storage = StorageAgent(db)

# Sample data
sample_schema = {
    "date": "2025-04-05",
    "amount": 7.85,
    "merchant": "Starbucks Reserve",
    "mood_vibe": "Calm and Enjoying a Premium Experience"
}

tx_id = storage.insert_transaction(
    transaction_date="2025-04-05",
    amount=7.85,
    merchant_name="Starbucks Reserve",
    document_type="receipt",
    source_path="input/receipts/2025/april/starbucks.pdf",
    raw_text="STARBUCKS RESERVE\nApril 5, 2025\nTotal: $7.85",
    agent_schema=sample_schema,
    batch_id=str(uuid.uuid4())
)

print(f"💾 Stored transaction with ID: {tx_id}")

# Query DB to verify
from sqlalchemy.orm import sessionmaker
Session = sessionmaker(bind=db.engine)
session = Session()
result = session.query(FinexaTransaction).filter_by(id=tx_id).first()
session.close()

if result:
    print(f"🔍 Retrieved: {result.merchant_name} - ${result.amount}")
else:
    print("❌ Transaction not found in DB")

from src.core.database import FinexaDatabase
from src.agents.storage_agent import StorageAgent
from src.agents.linker_agent import LinkerAgent
from src.core.config import config
import uuid

# Initialize DB
db = FinexaDatabase(config.DB_URL)

# Initialize Agents
storage = StorageAgent(db)
linker = LinkerAgent(db, config.DASHSCOPE_API_KEY)

# Use same batch_id for both transactions
batch_id = str(uuid.uuid4())

# Insert TX1
tx1_id = storage.insert_transaction(
    transaction_date="2025-04-05",
    amount=7.85,
    merchant_name="Starbucks Reserve",
    document_type="receipt",
    source_path="input/receipts/2025/april/receipt1.pdf",
    raw_text="STARBUCKS RESERVE\nApril 5, 2025\nTotal: $7.85",
    agent_schema={"merchant": "Starbucks Reserve", "amount": 7.85, "date": "2025-04-05"},
    batch_id=batch_id
)

# Insert TX2
tx2_id = storage.insert_transaction(
    transaction_date="2025-04-05",
    amount=7.85,
    merchant_name="Starbucks Downtown",
    document_type="statement_line",
    source_path="input/statements/2025/q1/statement_april.csv:L47",
    raw_text="STARBUCKS DOWNTOWN, $7.85, 2025-04-05",
    agent_schema={"merchant": "Starbucks Downtown", "amount": 7.85, "date": "2025-04-05"},
    batch_id=batch_id
)

print(f"💾 Stored TX1: {tx1_id}, TX2: {tx2_id}")

# Run linker on TX2 — with batch_id
linker.find_and_link_matches(tx2_id, batch_id)

# Verify linking
tx1 = db.get_transaction_by_id(tx1_id)
tx2 = db.get_transaction_by_id(tx2_id)

print(f"🔗 TX1 linked_id: {tx1.linked_id}")
print(f"🔗 TX2 linked_id: {tx2.linked_id}")

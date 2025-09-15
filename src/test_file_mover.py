from pathlib import Path  # ← FIXED: Import Path
from src.agents.file_mover import FileMoverAgent

# Create a test file if not exists
test_file = "input/receipts/2025/april/test_receipt.pdf"
Path(test_file).parent.mkdir(parents=True, exist_ok=True)
with open(test_file, "w") as f:
    f.write("%PDF-1.4 test")

# Initialize mover
mover = FileMoverAgent()

# Move it
mover.move_to_processed(test_file)

# Check if moved
if not Path(test_file).exists():
    print("✅ File moved successfully")
else:
    print("❌ File not moved")

import uuid
import time
from datetime import datetime
from src.agents.file_scanner import FileScannerAgent
from src.agents.document_classifier import DocumentClassifierAgent
from src.agents.text_extractor import TextExtractorAgent
from src.agents.transaction_splitter import TransactionSplitterAgent
from src.agents.schema_architect import SchemaArchitectAgent
from src.agents.storage_agent import StorageAgent
from src.agents.linker_agent import LinkerAgent
from src.agents.file_mover import FileMoverAgent
from src.core.database import FinexaDatabase
from src.core.config import config
import json

def format_time(seconds):
    """Format seconds into HH:MM:SS."""
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    return f"{h:02d}:{m:02d}:{s:02d}"

def main():
    """FINEXA: Autonomous Financial Nexus Agent — NASA-GRADE"""
    print("🚀 FINEXA: MISSION START — AUTONOMOUS FINANCIAL INTELLIGENCE")
    
    # Initialize agents
    db = FinexaDatabase(config.DB_PATH)
    file_scanner = FileScannerAgent()
    classifier = DocumentClassifierAgent()
    extractor = TextExtractorAgent()
    splitter = TransactionSplitterAgent()
    architect = SchemaArchitectAgent()
    storage = StorageAgent(db)
    linker = LinkerAgent(db, config.DASHSCOPE_API_KEY)
    mover = FileMoverAgent()
    
    # Generate batch_id
    batch_id = str(uuid.uuid4())
    
    # Scan PDFs
    pdf_paths = file_scanner.find_all_pdfs()
    total_pdfs = len(pdf_paths)
    print(f"📁 Found {total_pdfs} PDFs")
    
    if total_pdfs == 0:
        print("🎉 FINEXA: MISSION COMPLETE — NO PDFs TO PROCESS")
        return
    
    # Track progress
    start_time = time.time()
    processed_pdfs = 0
    total_transactions = 0

    # Process each PDF
    for pdf_path in pdf_paths:
        try:
            processed_pdfs += 1
            print(f"\n📄 Processing PDF {processed_pdfs}/{total_pdfs}: {pdf_path}")
            
            # Classify
            document_type = classifier.classify_document_type(str(pdf_path))
            print(f"🏷️ Classified as: {document_type}")
            
            # Extract text
            result = extractor.extract_raw_text(str(pdf_path))
            raw_text = result["raw_text"]
            is_image_based = result["is_image_based"]
            print(f"🔤 Extracted {len(raw_text)} chars")
            
            # Split into transactions
            transaction_texts = splitter.split_transactions(raw_text, document_type)
            print(f"✂️  Split into {len(transaction_texts)} transactions")
            
            # Process each transaction
            pdf_transaction_count = 0
            for i, tx_text in enumerate(transaction_texts):
                try:
                    print(f"  🧾 Processing transaction {i+1}/{len(transaction_texts)}")
                    
                    # Convert tx_text to string if dict
                    if isinstance(tx_text, dict):
                        raw_text_str = json.dumps(tx_text, ensure_ascii=False)
                    else:
                        raw_text_str = str(tx_text)
                    
                    # Generate schema
                    agent_schema = architect.generate_agent_schema(tx_text, document_type)
                    
                    # FORCE agent_schema to be a DICT
                    if not isinstance(agent_schema, dict):
                        agent_schema = {"error": "agent_schema is not a dict", "raw": str(agent_schema)}
                    
                    merchant = agent_schema.get("merchant", "Unknown")
                    amount = float(agent_schema.get("amount", 0.0))
                    print(f"    🎨 Schema: {merchant} - ${amount}")
                    
                    # Store
                    tx_id = storage.insert_transaction(
                        transaction_date=agent_schema.get("date", "2025-01-01"),
                        amount=amount,
                        merchant_name=merchant,
                        document_type=document_type,
                        source_path=str(pdf_path),
                        raw_text=raw_text_str,  # ← FIXED: NOW A STRING
                        agent_schema=agent_schema,
                        batch_id=batch_id
                    )
                    print(f"    💾 Stored with ID: {tx_id}")
                    
                    # Link
                    linker.find_and_link_matches(tx_id, batch_id)
                    print(f"    🔗 Linked to match (if any)")
                    
                    total_transactions += 1
                    pdf_transaction_count += 1
                    
                except Exception as e:
                    print(f"    ❌ Failed transaction {i+1}: {str(e)}")
                    continue
            
            # Move PDF only after ALL transactions processed
            mover.move_to_processed(str(pdf_path))
            print(f"✅ DONE: {pdf_path} → {pdf_transaction_count} transactions stored")
            
            # Update ETA
            current_time = time.time()
            elapsed_time = current_time - start_time
            avg_time_per_pdf = elapsed_time / processed_pdfs if processed_pdfs > 0 else 0
            remaining_pdfs = total_pdfs - processed_pdfs
            estimated_remaining_time = avg_time_per_pdf * remaining_pdfs
            eta = format_time(int(estimated_remaining_time))
            
            print(f"📊 PROGRESS: {processed_pdfs}/{total_pdfs} PDFs | {total_transactions} transactions total")
            print(f"⏱️  ETA: {eta} | Avg: {avg_time_per_pdf:.1f}s/PDF")
            
        except Exception as e:
            print(f"❌ FAILED PDF {pdf_path}: {str(e)}")
            continue
    
    total_time = time.time() - start_time
    print(f"\n🎉 FINEXA: MISSION COMPLETE — FINANCIAL NEXUS ESTABLISHED")
    print(f"⏱️  Total time: {format_time(int(total_time))}")
    print(f"📈 Processed {total_transactions} transactions from {processed_pdfs} PDFs")

if __name__ == "__main__":
    main()

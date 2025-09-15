from typing import TypedDict, List, Annotated
from langgraph.graph import StateGraph, END
from src.core.config import config
from src.core.database import FinexaDatabase
from src.agents.file_scanner import FileScannerAgent
from src.agents.document_classifier import DocumentClassifierAgent
from src.agents.text_extractor import TextExtractorAgent
from src.agents.schema_architect import SchemaArchitectAgent
from src.agents.storage_agent import StorageAgent
from src.agents.linker_agent import LinkerAgent
from src.agents.file_mover import FileMoverAgent
import operator
import uuid

# Define AppState
class AppState(TypedDict):
    pdf_paths: List[str]
    current_pdf: str
    document_type: str
    raw_text: str
    is_image_based: bool
    agent_schema: dict
    transaction_id: int
    batch_id: str
    errors: Annotated[list, operator.add]

# Initialize agents
db = FinexaDatabase(config.DB_URL)
file_scanner = FileScannerAgent()
classifier = DocumentClassifierAgent()
extractor = TextExtractorAgent()
architect = SchemaArchitectAgent()
storage = StorageAgent(db)
linker = LinkerAgent(db, config.DASHSCOPE_API_KEY)
mover = FileMoverAgent()

# Define nodes
def scan_files_node(state: AppState) -> dict:
    """Scan input folder for PDFs."""
    pdfs = file_scanner.find_all_pdfs()
    pdf_paths = [str(p) for p in pdfs]
    print(f"📁 Found {len(pdf_paths)} PDFs")
    return {"pdf_paths": pdf_paths}

def process_next_pdf_node(state: AppState) -> dict:
    """Get next PDF to process."""
    if not state["pdf_paths"]:
        return {"current_pdf": None}
    current_pdf = state["pdf_paths"].pop(0)
    print(f"📄 Processing: {current_pdf}")
    return {"current_pdf": current_pdf}

def classify_document_node(state: AppState) -> dict:
    """Classify PDF as receipt or statement_line."""
    doc_type = classifier.classify_document_type(state["current_pdf"])
    print(f"🏷️ Classified as: {doc_type}")
    return {"document_type": doc_type}

def extract_text_node(state: AppState) -> dict:
    """Extract raw text from PDF."""
    result = extractor.extract_raw_text(state["current_pdf"])
    print(f"🔤 Extracted {len(result['raw_text'])} chars")
    return {
        "raw_text": result["raw_text"],
        "is_image_based": result["is_image_based"]
    }

def generate_schema_node(state: AppState) -> dict:
    """Generate dynamic schema using Qwen-Max."""
    schema = architect.generate_agent_schema(state["raw_text"], state["document_type"])
    print(f"🎨 Schema generated with {len(schema)} fields")
    return {"agent_schema": schema}

def store_transaction_node(state: AppState) -> dict:
    """Store transaction in DB."""
    # Extract required fields from schema
    schema = state["agent_schema"]
    tx_id = storage.insert_transaction(
        transaction_date=schema.get("date", "2025-01-01"),
        amount=float(schema.get("amount", 0.0)),
        merchant_name=schema.get("merchant", "Unknown"),
        document_type=state["document_type"],
        source_path=state["current_pdf"],
        raw_text=state["raw_text"],
        agent_schema=schema,
        batch_id=state["batch_id"]
    )
    print(f"💾 Stored with ID: {tx_id}")
    return {"transaction_id": tx_id}

def link_transaction_node(state: AppState) -> dict:
    """Link transaction to existing records."""
    linker.find_and_link_matches(state["transaction_id"], state["batch_id"])
    print(f"🔗 Linking completed for ID: {state['transaction_id']}")
    return {}

def move_file_node(state: AppState) -> dict:
    """Move processed file to /processed/."""
    mover.move_to_processed(state["current_pdf"])
    print(f"📂 File moved: {state['current_pdf']}")
    return {}

# Build graph
workflow = StateGraph(AppState)

# Add nodes
workflow.add_node("scan_files", scan_files_node)
workflow.add_node("process_next_pdf", process_next_pdf_node)
workflow.add_node("classify_document", classify_document_node)
workflow.add_node("extract_text", extract_text_node)
workflow.add_node("generate_schema", generate_schema_node)
workflow.add_node("store_transaction", store_transaction_node)
workflow.add_node("link_transaction", link_transaction_node)
workflow.add_node("move_file", move_file_node)

# Set entry point
workflow.set_entry_point("scan_files")

# Define edges
workflow.add_edge("scan_files", "process_next_pdf")

def continue_or_end(state: AppState):
    if state["current_pdf"] is None:
        return END
    return "classify_document"

workflow.add_conditional_edges(
    "process_next_pdf",
    continue_or_end,
    {
        "classify_document": "classify_document",
        END: END
    }
)

workflow.add_edge("classify_document", "extract_text")
workflow.add_edge("extract_text", "generate_schema")
workflow.add_edge("generate_schema", "store_transaction")
workflow.add_edge("store_transaction", "link_transaction")
workflow.add_edge("link_transaction", "move_file")
workflow.add_edge("move_file", "process_next_pdf")

# Compile
app = workflow.compile()

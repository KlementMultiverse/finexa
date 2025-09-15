from src.orchestrator.finexa_orchestrator import app
import uuid

def main():
    """FINEXA: Autonomous Financial Nexus Agent — NASA-GRADE"""
    print("🚀 FINEXA: MISSION START — AUTONOMOUS FINANCIAL INTELLIGENCE")
    
    # Initialize state
    initial_state = {
        "pdf_paths": [],
        "current_pdf": None,
        "document_type": "",
        "raw_text": "",
        "is_image_based": False,
        "agent_schema": {},
        "transaction_id": 0,
        "batch_id": str(uuid.uuid4()),
        "errors": []
    }
    
    try:
        # Run the graph
        final_state = app.invoke(initial_state)
        print("🎉 FINEXA: MISSION COMPLETE — FINANCIAL NEXUS ESTABLISHED")
        
    except Exception as e:
        print(f"❌ Mission failed: {str(e)}")

if __name__ == "__main__":
    main()

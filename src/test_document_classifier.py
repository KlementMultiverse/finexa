from src.agents.document_classifier import DocumentClassifierAgent

classifier = DocumentClassifierAgent()

# Test with our fake PDFs
test_files = [
    "input/receipts/2025/april/starbucks.pdf",
    "input/statements/2025/q1/april_statement.pdf"
]

for pdf_path in test_files:
    doc_type = classifier.classify_document_type(pdf_path)
    print(f"📄 {pdf_path} → {doc_type}")

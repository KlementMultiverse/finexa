from src.agents.text_extractor import TextExtractorAgent

extractor = TextExtractorAgent()

test_files = [
    "input/receipts/2025/april/starbucks.pdf",
    "input/statements/2025/q1/april_statement.pdf"
]

for pdf_path in test_files:
    result = extractor.extract_raw_text(pdf_path)
    print(f"📄 {pdf_path}")
    print(f"   → is_image_based: {result['is_image_based']}")
    print(f"   → raw_text length: {len(result['raw_text'])} chars")
    print(f"   → preview: {result['raw_text'][:100]}...")
    print()

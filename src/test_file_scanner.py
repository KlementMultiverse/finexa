from src.agents.file_scanner import FileScannerAgent  # ← ABSOLUTE IMPORT

scanner = FileScannerAgent()
pdfs = scanner.find_all_pdfs()
print(f"Found {len(pdfs)} PDFs:")
for p in pdfs:
    print(f"  → {p}")

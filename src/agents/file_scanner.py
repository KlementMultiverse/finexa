from pathlib import Path
from typing import List
from src.core.config import config  # ← ABSOLUTE IMPORT

class FileScannerAgent:
    """Agent that scans input folder for PDFs — recursive, preserves structure."""
    
    def __init__(self, input_dir: str = None):
        self.input_dir = Path(input_dir or config.INPUT_DIR)
    
    def find_all_pdfs(self) -> List[Path]:
        """Find all PDFs in input_dir and subfolders."""
        if not self.input_dir.exists():
            self.input_dir.mkdir(parents=True, exist_ok=True)
        return list(self.input_dir.rglob("*.pdf"))

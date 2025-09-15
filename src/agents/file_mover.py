from pathlib import Path
import shutil
from src.core.config import config

class FileMoverAgent:
    """Agent that moves processed PDFs to /processed/ folder, preserving structure."""
    
    def __init__(self, input_dir: str = None, processed_dir: str = None):
        self.input_dir = Path(input_dir or config.INPUT_DIR)
        self.processed_dir = Path(processed_dir or config.PROCESSED_DIR)
    
    def move_to_processed(self, pdf_path: str):
        """Move PDF to processed folder, mirror subfolder structure."""
        pdf_path = Path(pdf_path)
        
        # Compute relative path
        try:
            relative_path = pdf_path.relative_to(self.input_dir)
        except ValueError:
            # If not under input_dir, use original name
            relative_path = pdf_path.name
        
        # Compute target path
        target_path = self.processed_dir / relative_path
        target_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Move file
        shutil.move(str(pdf_path), str(target_path))
        print(f"📂 Moved: {pdf_path} → {target_path}")

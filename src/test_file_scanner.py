
# Add comprehensive error handling
import logging
import sys
from functools import wraps

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def handle_errors(func):
    """Decorator for error handling"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.error(f"Error in {func.__name__}: {e}")
            raise
    return wrapper


from src.agents.file_scanner import FileScannerAgent  # ← ABSOLUTE IMPORT

scanner = FileScannerAgent()
pdfs = scanner.find_all_pdfs()
print(f"Found {len(pdfs)} PDFs:")
for p in pdfs:
    print(f"  → {p}")

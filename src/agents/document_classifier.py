import os
from PyPDF2 import PdfReader
from openai import OpenAI
from src.core.config import config

class DocumentClassifierAgent:
    """Agent that classifies a PDF as 'receipt' or 'statement_line' using Qwen-Max."""
    
    def __init__(self):
        self.client = OpenAI(
            api_key=config.DASHSCOPE_API_KEY,
            base_url=config.BASE_URL
        )
    
    def extract_text_preview(self, pdf_path: str, max_chars: int = 500) -> str:
        """Extract first few characters from PDF (text-based only)."""
        try:
            reader = PdfReader(pdf_path)
            text = ""
            for page in reader.pages:
                text += page.extract_text() or ""
                if len(text) > max_chars:
                    break
            return text[:max_chars]
        except Exception:
            return ""
    
    def classify_document_type(self, pdf_path: str) -> str:
        """Classify PDF as 'receipt' or 'statement_line' using Qwen-Max."""
        # Try to extract text first
        text_preview = self.extract_text_preview(pdf_path)
        
        if not text_preview.strip():
            # If no text → assume it's a scanned receipt
            return "receipt"
        
        # Ask Qwen-Max to classify
        prompt = f"""
        Classify this financial document as either "receipt" or "statement_line".

        Document Preview:
        {text_preview}

        Rules:
        - "receipt" = merchant receipt, invoice, purchase confirmation
        - "statement_line" = bank/credit card statement entry, transaction log

        Answer ONLY with one word: "receipt" or "statement_line"
        """
        
        response = self.client.chat.completions.create(
            model=config.MODEL_MAX,
            messages=[{"role": "user", "content": prompt}]
        )
        
        result = response.choices[0].message.content.strip().lower()
        if "receipt" in result:
            return "receipt"
        elif "statement" in result:
            return "statement_line"
        else:
            # Fallback
            return "receipt"

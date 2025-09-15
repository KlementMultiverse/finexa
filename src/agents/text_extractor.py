import os
from pathlib import Path
from PyPDF2 import PdfReader
from pdf2image import convert_from_path
from openai import OpenAI
from src.core.config import config

class TextExtractorAgent:
    """Agent that extracts raw text from PDF — text-based or image-based."""
    
    def __init__(self):
        self.client = OpenAI(
            api_key=config.DASHSCOPE_API_KEY,
            base_url=config.BASE_URL
        )
    
    def extract_text_pypdf2(self, pdf_path: str) -> str:
        """Extract text using PyPDF2 (for text-based PDFs)."""
        try:
            reader = PdfReader(pdf_path)
            text = ""
            for page in reader.pages:
                extracted = page.extract_text()
                if extracted:
                    text += extracted + "\n"
            return text.strip()
        except Exception:
            return ""
    
    def extract_text_qwen_vl(self, pdf_path: str) -> str:
        """Extract text using Qwen-VL (for image-based/scanned PDFs)."""
        try:
            # Convert first page to image
            images = convert_from_path(pdf_path, first_page=1, last_page=1, dpi=200)
            if not images:
                return ""
            
            # Save image to temp file
            temp_image = Path("temp_page.jpg")
            images[0].save(temp_image, "JPEG")
            
            # Send to Qwen-VL
            with open(temp_image, "rb") as image_file:
                import base64
                image_base64 = base64.b64encode(image_file.read()).decode("utf-8")
            
            # Clean up
            temp_image.unlink()
            
            response = self.client.chat.completions.create(
                model=config.MODEL_VL_PLUS,  # Use VL-Plus for cost efficiency
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}},
                            {"type": "text", "text": "Extract ALL visible text from this image. Return only the raw text, no formatting, no explanations."}
                        ]
                    }
                ],
                max_tokens=2000
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            print(f"⚠️ Qwen-VL extraction failed: {str(e)}")
            return ""
    
    def extract_raw_text(self, pdf_path: str) -> dict:
        """Extract raw text + flag if image-based."""
        # First, try text extraction
        raw_text = self.extract_text_pypdf2(pdf_path)
        
        if raw_text.strip():
            return {
                "raw_text": raw_text,
                "is_image_based": False
            }
        else:
            # Fallback to Qwen-VL
            raw_text = self.extract_text_qwen_vl(pdf_path)
            return {
                "raw_text": raw_text,
                "is_image_based": True
            }

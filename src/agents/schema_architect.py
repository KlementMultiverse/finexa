import json
from openai import OpenAI
from src.core.config import config

class SchemaArchitectAgent:
    """Agent that generates dynamic JSON schema from raw text using Qwen-Max."""
    
    def __init__(self):
        self.client = OpenAI(
            api_key=config.DASHSCOPE_API_KEY,
            base_url=config.BASE_URL
        )
    
    def generate_agent_schema(self, raw_text: str, document_type: str) -> dict:
        """Generate dynamic schema from raw text."""
        if not raw_text.strip():
            return {"error": "No text to process"}
        
        prompt = f"""
        You are a Financial Schema Architect AI.

        Document Type: {document_type}
        Raw Text:
        {raw_text}

        Extract ALL meaningful fields you can infer — even unconventional ones.
        Think creatively: time of day, mood, purpose, location, payment friction, loyalty status, etc.

        Return JSON only. No explanation. No markdown. No extra text.

        Example Output:
        {{
            "date": "2025-04-05",
            "amount": 7.85,
            "currency": "USD",
            "merchant": "Starbucks Reserve",
            "time_of_day": "Morning",
            "purpose_guess": "Commute Fuel",
            "mood_vibe": "Rushed but Happy",
            "receipt_confidence": 0.98
        }}
        """
        
        try:
            response = self.client.chat.completions.create(
                model=config.MODEL_MAX,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1000
            )
            
            content = response.choices[0].message.content.strip()
            
            # Try to parse as JSON
            try:
                return json.loads(content)
            except json.JSONDecodeError:
                # Fallback: return as text
                return {"raw_output": content, "error": "JSON parse failed"}
                
        except Exception as e:
            return {"error": str(e)}

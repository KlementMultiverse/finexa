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
    
    def generate_agent_schema(self, input_data, document_type: str) -> dict:
        """Generate dynamic schema from raw text or dict — ALWAYS RETURNS DICT."""
        # Convert dict to string if needed
        if isinstance(input_data, dict):
            raw_text = json.dumps(input_data, indent=2)
        else:
            raw_text = str(input_data)
        
        if not raw_text.strip():
            return {"error": "No text to process"}
        
        prompt = f"""
        You are a Financial Schema Architect AI.

        Document Type: {document_type}
        Raw Data:
        {raw_text}

        Extract ALL meaningful fields — even unconventional ones.
        Think creatively: time of day, mood, purpose, location, etc.

        Return JSON only. No explanations.

        Example Output:
        {{
            "date": "2025-04-05",
            "amount": 7.85,
            "currency": "USD",
            "merchant": "Starbucks Reserve",
            "time_of_day": "Morning",
            "purpose_guess": "Commute Fuel"
        }}
        """
        
        try:
            response = self.client.chat.completions.create(
                model=config.MODEL_MAX,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1000
            )
            
            content = response.choices[0].message.content.strip()
            
            # Try to parse as JSON → if fails → return error dict
            try:
                parsed = json.loads(content)
                if isinstance(parsed, dict):
                    return parsed
                else:
                    return {"error": "Not a JSON object", "raw_output": content}
            except json.JSONDecodeError:
                return {"error": "JSON parse failed", "raw_output": content}
                
        except Exception as e:
            return {"error": str(e), "raw_output": ""}

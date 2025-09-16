import json
import re
from openai import OpenAI
from ..core.config import config

class SchemaArchitectAgent:
    def __init__(self):
        self.client = OpenAI(api_key=config.DASHSCOPE_API_KEY, base_url=config.BASE_URL)
    
    def generate_agent_schema(self, input_data, document_type):
        """Generate schema with intelligent fallbacks - never return Unknown"""
        
        if isinstance(input_data, dict):
            raw_text = json.dumps(input_data, indent=2)
        else:
            raw_text = str(input_data)
        
        if not raw_text.strip():
            return {"error": "No text provided"}
        
        # Enhanced prompt that forces meaningful descriptions
        prompt = f"""
        Analyze this bank transaction and extract structured data:
        
        Transaction: {raw_text}
        
        Extract these fields in JSON format:
        - date: Transaction date (YYYY-MM-DD)
        - amount: Number (negative for expenses, positive for income)
        - merchant: Business name OR descriptive transaction type
        - category: Spending category
        - description: Brief description
        
        CRITICAL RULES:
        1. NEVER use "Unknown" - always provide a descriptive name
        2. If no clear merchant, use transaction type like:
           - "ATM Withdrawal" 
           - "Bank Transfer"
           - "Direct Deposit"
           - "Service Fee"
           - "Interest Payment"
           - "Check Deposit"
           - "Online Transfer"
        3. Make it human-readable and meaningful
        
        Examples:
        - "10/05 ATM WITHDRAWAL -160.00" → merchant: "ATM Withdrawal"
        - "ZELLE PAYMENT FROM JOHN" → merchant: "Zelle from John"
        - "AUTOPAY CREDIT CARD" → merchant: "Credit Card Payment"
        
        Return JSON only:
        """
        
        try:
            response = self.client.chat.completions.create(
                model=config.MODEL_MAX,
                messages=[
                    {"role": "system", "content": "You are a financial analyst. Always provide meaningful, human-readable transaction descriptions. Never use 'Unknown' or generic terms."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=800,
                temperature=0.2
            )
            
            content = response.choices[0].message.content.strip()
            
            # Clean JSON response
            if content.startswith('```json'):
                content = content.replace('```json', '').replace('```', '').strip()
            elif content.startswith('```'):
                content = content.replace('```', '').strip()
            
            try:
                schema = json.loads(content)
                
                # Final validation - ensure no "Unknown" values
                schema = self.ensure_meaningful_fields(schema, raw_text)
                return schema
                
            except json.JSONDecodeError:
                return self.create_intelligent_fallback(raw_text)
                
        except Exception as e:
            return self.create_intelligent_fallback(raw_text)
    
    def ensure_meaningful_fields(self, schema, raw_text):
        """Ensure all fields have meaningful values"""
        
        if not isinstance(schema, dict):
            return self.create_intelligent_fallback(raw_text)
        
        # Fix merchant field if it's generic
        merchant = schema.get("merchant", "").strip()
        if not merchant or merchant.lower() in ["unknown", "", "n/a", "na", "merchant", "transaction"]:
            schema["merchant"] = self.generate_smart_merchant_name(raw_text)
        
        # Ensure amount is valid
        try:
            schema["amount"] = float(schema.get("amount", 0))
        except (ValueError, TypeError):
            schema["amount"] = self.extract_amount_from_text(raw_text)
        
        # Set meaningful defaults
        schema.setdefault("currency", "USD")
        schema.setdefault("date", "2025-01-01")
        schema.setdefault("category", self.smart_categorize(schema["merchant"], raw_text))
        schema.setdefault("description", schema["merchant"])
        
        return schema
    
    def generate_smart_merchant_name(self, text):
        """Generate meaningful merchant name from transaction text"""
        text_lower = text.lower()
        
        # Transaction type patterns
        if any(word in text_lower for word in ['atm', 'withdrawal', 'cash']):
            return "ATM Withdrawal"
        elif any(word in text_lower for word in ['transfer', 'zelle', 'venmo']):
            return "Money Transfer"
        elif any(word in text_lower for word in ['deposit', 'payroll', 'direct dep']):
            return "Direct Deposit"
        elif any(word in text_lower for word in ['fee', 'service', 'maintenance']):
            return "Bank Fee"
        elif any(word in text_lower for word in ['interest', 'dividend']):
            return "Interest Payment"
        elif any(word in text_lower for word in ['check', 'chk']):
            return "Check Transaction"
        elif any(word in text_lower for word in ['payment', 'autopay', 'bill pay']):
            return "Bill Payment"
        elif any(word in text_lower for word in ['refund', 'credit', 'return']):
            return "Refund/Credit"
        elif any(word in text_lower for word in ['purchase', 'pos', 'debit']):
            # Try to extract a business name from purchase
            words = text.split()
            for word in words:
                if len(word) > 4 and not re.match(r'^\d+[\.\-/]*\d*$', word):
                    return f"Purchase at {word.title()}"
            return "Card Purchase"
        else:
            # Extract any meaningful text
            words = re.findall(r'\b[A-Za-z]{3,}\b', text)
            if words:
                return f"Transaction: {words[0].title()}"
            return "Bank Transaction"
    
    def extract_amount_from_text(self, text):
        """Extract amount from transaction text"""
        amount_match = re.search(r'[\-\$]?(\d+\.?\d*)', text)
        if amount_match:
            amount = float(amount_match.group(1))
            # Check if it should be negative
            if '-' in text or any(word in text.lower() for word in ['debit', 'withdrawal', 'fee', 'payment']):
                return -abs(amount)
            return amount
        return 0.0
    
    def smart_categorize(self, merchant, text):
        """Smart categorization based on merchant and text"""
        merchant_lower = merchant.lower()
        text_lower = text.lower()
        
        if any(word in merchant_lower for word in ['atm', 'withdrawal', 'cash']):
            return 'Cash & ATM'
        elif any(word in merchant_lower for word in ['transfer', 'zelle', 'venmo', 'payment']):
            return 'Transfers & Payments'
        elif any(word in merchant_lower for word in ['deposit', 'payroll', 'salary']):
            return 'Income'
        elif any(word in merchant_lower for word in ['fee', 'service', 'maintenance']):
            return 'Bank Fees'
        elif any(word in merchant_lower for word in ['interest', 'dividend']):
            return 'Interest & Dividends'
        elif any(word in merchant_lower for word in ['gas', 'fuel', 'shell', 'bp']):
            return 'Gas & Fuel'
        elif any(word in merchant_lower for word in ['grocery', 'market', 'food']):
            return 'Groceries'
        elif any(word in merchant_lower for word in ['restaurant', 'cafe', 'dining']):
            return 'Dining'
        elif any(word in merchant_lower for word in ['amazon', 'store', 'shop']):
            return 'Shopping'
        else:
            return 'Other'
    
    def create_intelligent_fallback(self, raw_text):
        """Create intelligent fallback schema"""
        return {
            "date": "2025-01-01",
            "amount": self.extract_amount_from_text(raw_text),
            "currency": "USD",
            "merchant": self.generate_smart_merchant_name(raw_text),
            "category": self.smart_categorize(self.generate_smart_merchant_name(raw_text), raw_text),
            "description": f"Transaction: {raw_text[:50]}...",
            "extraction_method": "intelligent_fallback",
            "confidence": "medium"
        }

import json
import re
from openai import OpenAI
from src.core.config import config

class TransactionSplitterAgent:
    """Agent that splits raw text into individual transactions using Qwen-Max."""
    
    def __init__(self):
        self.client = OpenAI(
            api_key=config.DASHSCOPE_API_KEY,
            base_url=config.BASE_URL
        )
    
    def pre_filter_transactions(self, raw_text: str) -> list:
        """Pre-filter raw text to extract only transaction lines."""
        lines = raw_text.split("\n")
        transaction_lines = []
        
        # Pattern: Starts with MM/DD or MM-DD, has amount with $ or -, ends with number
        pattern = r'^\d{1,2}[/-]\d{1,2}.*?[\$\-\d\.]+\s*\d*\.?\d{0,2}$'
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            # Skip noise lines
            if any(x in line for x in ["*start*", "*end*", "Page of", "SM SM", "CUSTOMER SERVICE"]):
                continue
            # Match transaction pattern
            if re.search(pattern, line):
                transaction_lines.append(line)
        
        return transaction_lines
    
    def split_transactions(self, raw_text: str, document_type: str) -> list:
        """Split raw text into individual transactions."""
        if not raw_text.strip():
            return []
        
        # Pre-filter to get clean transaction lines
        clean_lines = self.pre_filter_transactions(raw_text)
        print(f"🔍 Pre-filtered {len(clean_lines)} transaction lines from {len(raw_text.splitlines())} total lines")
        
        if not clean_lines:
            return [{"date": "1970-01-01", "description": "NO TRANSACTIONS FOUND", "amount": 0.0, "type": "unknown"}]
        
        # Join clean lines for Qwen-Max
        clean_text = "\n".join(clean_lines)
        
        prompt = f"""
        You are a Financial Transaction Extractor AI.

        INSTRUCTIONS:
        - Extract EVERY transaction from the text below.
        - IGNORE headers, footers, ads, page numbers, noise.
        - Each transaction has: DATE, DESCRIPTION, AMOUNT.
        - AMOUNT is negative for withdrawals, positive for deposits.
        - Return ONLY a JSON array of objects with keys: "date" (YYYY-MM-DD), "description", "amount" (float).

        EXAMPLE:
        Input: "10/05 ATM Withdrawal 10/05 695 Thornton Pkwy Thornton CO Card 0226 -160.00 214.27"
        Output: [{{"date": "2023-10-05", "description": "ATM Withdrawal 695 Thornton Pkwy Thornton CO Card 0226", "amount": -160.0}}]

        TEXT TO PROCESS:
        {clean_text}

        OUTPUT JSON ONLY. NO EXPLANATIONS.
        """
        
        try:
            response = self.client.chat.completions.create(
                model=config.MODEL_MAX,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=2000
            )
            
            content = response.choices[0].message.content.strip()
            
            # Try to parse as JSON
            try:
                transactions = json.loads(content)
                if isinstance(transactions, list):
                    return transactions
                else:
                    raise ValueError("Not a list")
            except (json.JSONDecodeError, ValueError):
                # Fallback: Regex extraction
                return self.fallback_extract(clean_lines)
                
        except Exception as e:
            print(f"❌ Qwen-Max failed: {str(e)}")
            return self.fallback_extract(clean_lines)
    
    def fallback_extract(self, lines: list) -> list:
        """Fallback: Extract transactions using regex."""
        transactions = []
        date_pattern = r'(\d{1,2})[/-](\d{1,2})'
        amount_pattern = r'[\$\s](-?\d+\.?\d{0,2})\s*$'
        
        for line in lines:
            # Extract date
            date_match = re.search(date_pattern, line)
            if not date_match:
                continue
            month, day = date_match.groups()
            date_str = f"2023-{month.zfill(2)}-{day.zfill(2)}"
            
            # Extract amount
            amount_match = re.search(amount_pattern, line)
            if not amount_match:
                continue
            amount = float(amount_match.group(1))
            
            # Extract description (everything between date and amount)
            desc_start = date_match.end()
            desc_end = amount_match.start()
            description = line[desc_start:desc_end].strip()
            
            transactions.append({
                "date": date_str,
                "description": description,
                "amount": amount,
                "type": "withdrawal" if amount < 0 else "deposit"
            })
        
        return transactions if transactions else [{"date": "1970-01-01", "description": "FALLBACK FAILED", "amount": 0.0, "type": "unknown"}]

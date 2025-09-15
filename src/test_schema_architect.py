from src.agents.schema_architect import SchemaArchitectAgent

architect = SchemaArchitectAgent()

# Fake receipt text
fake_receipt = """
STARBUCKS RESERVE
April 5, 2025
8:07 AM
Espresso: $4.50
Almond Croissant: $3.35
Total: $7.85
Paid with Apple Pay
"""

schema = architect.generate_agent_schema(fake_receipt, "receipt")
print("🎨 Generated Schema:")
print(schema)

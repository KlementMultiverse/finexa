import gradio as gr
import pandas as pd
import plotly.express as px
from src.core.database import FinexaDatabase, FinexaTransaction
from src.core.config import config
from openai import OpenAI

# Initialize DB and LLM
db = FinexaDatabase(config.DB_URL)
client = OpenAI(api_key=config.DASHSCOPE_API_KEY, base_url=config.BASE_URL)

def load_transactions():
    """Load all transactions for table display."""
    from sqlalchemy.orm import sessionmaker
    Session = sessionmaker(bind=db.engine)
    session = Session()
    transactions = session.query(FinexaTransaction).order_by(FinexaTransaction.transaction_date, FinexaTransaction.id).all()
    
    data = []
    for tx in transactions:
        data.append({
            "ID": tx.id,
            "Date": tx.transaction_date,
            "Amount": tx.amount,
            "Merchant": tx.merchant_name,
            "Type": tx.document_type,
            "Linked to": tx.linked_id or "—",
            "Src": tx.source_path
        })
    session.close()
    return pd.DataFrame(data)

def create_amount_chart():
    """Create bar chart of transaction amounts."""
    from sqlalchemy.orm import sessionmaker
    Session = sessionmaker(bind=db.engine)
    session = Session()
    transactions = session.query(FinexaTransaction).order_by(FinexaTransaction.amount.desc()).limit(10).all()
    session.close()
    
    df = pd.DataFrame([
        {"Merchant": tx.merchant_name, "Amount": tx.amount, "Date": tx.transaction_date}
        for tx in transactions
    ])
    
    fig = px.bar(df, x="Merchant", y="Amount", title="💰 Top 10 Transactions by Amount")
    return fig

def create_category_pie_chart():
    """Create pie chart of transaction categories."""
    from sqlalchemy.orm import sessionmaker
    Session = sessionmaker(bind=db.engine)
    session = Session()
    groups = session.query(FinexaTransaction.merchant_name, FinexaTransaction.amount)\
        .group_by(FinexaTransaction.merchant_name)\
        .order_by(FinexaTransaction.amount.desc())\
        .limit(5)\
        .all()
    session.close()
    
    df = pd.DataFrame(groups, columns=["merchant_name", "amount"])
    df.columns = ["Merchant", "Amount"]
    
    fig = px.pie(df, values="Amount", names="Merchant", title="🥧 Top 5 Merchants")
    return fig

def chat_with_data(question: str):
    """Chat with financial data using Qwen-Max."""
    from sqlalchemy.orm import sessionmaker
    Session = sessionmaker(bind=db.engine)
    session = Session()
    transactions = session.query(FinexaTransaction).order_by(FinexaTransaction.created_at.desc()).limit(20).all()
    session.close()
    
    context = "\n".join([
        f"ID:{tx.id} | {tx.transaction_date} | ${tx.amount} | {tx.merchant_name} | {tx.document_type}"
        for tx in transactions
    ])
    
    prompt = f"""
    You are FINEXA, NASA-grade financial AI assistant.
    Answer the user's question based on the last 20 transactions.

    Transactions:
    {context}

    Question: {question}

    Answer concisely in 1-2 sentences.
    """
    
    try:
        response = client.chat.completions.create(
            model=config.MODEL_MAX,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=200
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error: {str(e)}"

def get_linkage_report():
    """Generate linkage report."""
    from sqlalchemy.orm import sessionmaker
    Session = sessionmaker(bind=db.engine)
    session = Session()
    total = session.query(FinexaTransaction).count()
    linked = session.query(FinexaTransaction).filter(FinexaTransaction.linked_id.isnot(None)).count()
    unlinked = total - linked
    session.close()
    
    if total > 0:
        return f"""
        📊 **FINEXA LINKAGE REPORT**
        - Total Transactions: {total}
        - Linked Pairs: {linked}
        - Unlinked: {unlinked}
        - Linkage Rate: {linked/total*100:.1f}%
        """
    else:
        return "📊 **FINEXA LINKAGE REPORT**\n- No transactions yet."

# Build UI
with gr.Blocks(title="FINEXA Mission Control") as demo:
    gr.Markdown("# 🚀 FINEXA: NASA-GRADE FINANCIAL MISSION CONTROL")
    
    with gr.Tab("Transaction Explorer"):
        gr.Markdown("## 📋 All Transactions (Chronological Order)")
        df = load_transactions()
        gr.DataFrame(df, interactive=False)
    
    with gr.Tab("AI Chat"):
        gr.Markdown("## 💬 Chat with Your Financial Data")
        chat_input = gr.Textbox(label="Ask a question", placeholder="e.g., What was my largest expense last week?")
        chat_output = gr.Textbox(label="FINEXA Response")
        chat_btn = gr.Button("Ask FINEXA")
        chat_btn.click(chat_with_data, inputs=chat_input, outputs=chat_output)
        
        # Add charts
        gr.Markdown("## 📈 Top 10 Transactions by Amount")
        amount_chart = gr.Plot(create_amount_chart())  # ← FIXED: gr.Plot, not gr.Plotly
        
        gr.Markdown("## 🥧 Top 5 Merchants")
        category_chart = gr.Plot(create_category_pie_chart())  # ← FIXED: gr.Plot
    
    with gr.Tab("Linkage Report"):
        gr.Markdown("## 📊 Financial Nexus Status")
        report = get_linkage_report()
        gr.Markdown(report)
        refresh_btn = gr.Button("Refresh Report")
        refresh_btn.click(get_linkage_report, inputs=None, outputs=gr.Markdown())

# Launch
if __name__ == "__main__":
    demo.launch()

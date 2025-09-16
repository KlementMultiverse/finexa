import gradio as gr
import sqlite3
import json
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime, timedelta
import sys
import os

# Add the parent directory to the path so we can import from src
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.config import config

class MissionControlDashboard:
    def __init__(self):
        self.db_path = config.DB_PATH
    
    def get_database_stats(self):
        """Get basic statistics from the database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Total transactions
            cursor.execute("SELECT COUNT(*) FROM mission_transactions")
            total_transactions = cursor.fetchone()[0]
            
            # Total amount
            cursor.execute("SELECT SUM(amount) FROM mission_transactions")
            total_amount = cursor.fetchone()[0] or 0
            
            # Unique merchants
            cursor.execute("SELECT COUNT(DISTINCT merchant_name) FROM mission_transactions")
            unique_merchants = cursor.fetchone()[0]
            
            # Document types
            cursor.execute("SELECT document_type, COUNT(*) FROM mission_transactions GROUP BY document_type")
            doc_types = cursor.fetchall()
            
            conn.close()
            
            return {
                "total_transactions": total_transactions,
                "total_amount": total_amount,
                "unique_merchants": unique_merchants,
                "document_types": doc_types
            }
        except Exception as e:
            return {"error": str(e)}
    
    def get_transactions_data(self):
        """Get all transactions for visualization"""
        try:
            conn = sqlite3.connect(self.db_path)
            df = pd.read_sql_query("""
                SELECT 
                    id,
                    transaction_date,
                    amount,
                    merchant_name,
                    document_type,
                    batch_id,
                    created_at
                FROM mission_transactions
                ORDER BY transaction_date DESC
            """, conn)
            conn.close()
            return df
        except Exception as e:
            return pd.DataFrame()
    
    def create_spending_chart(self):
        """Create spending over time chart"""
        df = self.get_transactions_data()
        if df.empty:
            fig = go.Figure()
            fig.add_annotation(text="No data available", 
                             xref="paper", yref="paper",
                             x=0.5, y=0.5, showarrow=False)
            return fig
        
        # Convert date column
        df['transaction_date'] = pd.to_datetime(df['transaction_date'])
        
        # Group by date and sum amounts
        daily_spending = df.groupby('transaction_date')['amount'].sum().reset_index()
        
        fig = px.line(daily_spending, 
                     x='transaction_date', 
                     y='amount',
                     title='Daily Spending Over Time',
                     labels={'amount': 'Amount ($)', 'transaction_date': 'Date'})
        
        return fig
    
    def create_merchant_chart(self):
        """Create top merchants chart"""
        df = self.get_transactions_data()
        if df.empty:
            fig = go.Figure()
            fig.add_annotation(text="No data available", 
                             xref="paper", yref="paper",
                             x=0.5, y=0.5, showarrow=False)
            return fig
        
        # Group by merchant and sum amounts (absolute values for visualization)
        merchant_spending = df.groupby('merchant_name')['amount'].sum().abs().sort_values(ascending=False).head(10)
        
        fig = px.bar(x=merchant_spending.index, 
                    y=merchant_spending.values,
                    title='Top 10 Merchants by Spending',
                    labels={'x': 'Merchant', 'y': 'Amount ($)'})
        
        return fig
    
    def create_dashboard_interface(self):
        """Create the Gradio interface"""
        
        def refresh_stats():
            stats = self.get_database_stats()
            if "error" in stats:
                return f"Database Error: {stats['error']}", "", ""
            
            summary = f"""
            📊 **FINEXA Mission Control Dashboard**
            
            **Database Statistics:**
            - Total Transactions: {stats['total_transactions']:,}
            - Total Amount: ${stats['total_amount']:,.2f}
            - Unique Merchants: {stats['unique_merchants']:,}
            
            **Document Types:**
            """
            
            for doc_type, count in stats['document_types']:
                summary += f"\n- {doc_type}: {count:,} transactions"
            
            return summary
        
        def get_transactions_table():
            df = self.get_transactions_data()
            if df.empty:
                return "No transactions found"
            
            # Format the dataframe for display
            df['amount'] = df['amount'].apply(lambda x: f"${x:.2f}")
            df['transaction_date'] = pd.to_datetime(df['transaction_date']).dt.strftime('%Y-%m-%d')
            
            return df[['id', 'transaction_date', 'amount', 'merchant_name', 'document_type']].head(50)
        
        with gr.Blocks(title="FINEXA Mission Control") as interface:
            gr.Markdown("# 🚀 FINEXA Mission Control Dashboard")
            gr.Markdown("Autonomous Financial Intelligence System")
            
            with gr.Row():
                with gr.Column():
                    stats_output = gr.Markdown(refresh_stats())
                    refresh_btn = gr.Button("🔄 Refresh Data")
                
                with gr.Column():
                    spending_chart = gr.Plot(self.create_spending_chart())
            
            with gr.Row():
                merchant_chart = gr.Plot(self.create_merchant_chart())
            
            with gr.Row():
                gr.Markdown("## 📋 Recent Transactions")
                transactions_table = gr.Dataframe(
                    get_transactions_table(),
                    label="Latest 50 Transactions"
                )
            
            # Event handlers
            refresh_btn.click(
                fn=lambda: [refresh_stats(), self.create_spending_chart(), self.create_merchant_chart(), get_transactions_table()],
                outputs=[stats_output, spending_chart, merchant_chart, transactions_table]
            )
        
        return interface

def main():
    """Launch the mission control dashboard"""
    dashboard = MissionControlDashboard()
    interface = dashboard.create_dashboard_interface()
    
    print("🚀 Launching FINEXA Mission Control Dashboard...")
    print(f"📊 Database: {config.DB_PATH}")
    
    interface.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False
    )

if __name__ == "__main__":
    main()

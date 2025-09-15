from sqlalchemy import create_engine, Column, Integer, String, Float, Date, Boolean, JSON, ForeignKey, TIMESTAMP, and_, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta
import uuid
from .config import config

Base = declarative_base()

class FinexaTransaction(Base):
    __tablename__ = 'mission_transactions'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    transaction_date = Column(Date, nullable=False)
    amount = Column(Float, nullable=False)
    currency = Column(String(3), default='USD')
    merchant_name = Column(String, nullable=True)
    document_type = Column(String(20), nullable=False)
    source_path = Column(String, nullable=False)
    raw_text = Column(String, nullable=False)
    agent_schema = Column(JSON, nullable=False)
    linked_id = Column(Integer, ForeignKey('mission_transactions.id'), nullable=True)
    is_matched = Column(Boolean, default=False)
    batch_id = Column(String, nullable=False)
    created_at = Column(TIMESTAMP, default=datetime.utcnow)
    last_linked_at = Column(TIMESTAMP, nullable=True)

class FinexaDatabase:
    def __init__(self, db_url):
        self.engine = create_engine(db_url)
        Base.metadata.create_all(self.engine)
        Session = sessionmaker(bind=self.engine)
        self.session = Session()
    
    def insert_transaction(self, **kwargs):
        tx = FinexaTransaction(**kwargs)
        self.session.add(tx)
        self.session.commit()
        return tx.id
    
    def get_transaction_by_id(self, tx_id: int):
        return self.session.query(FinexaTransaction).filter_by(id=tx_id).first()
    
    def get_unlinked_transactions(self, date, amount, new_tx_id: int, batch_id: str, tolerance=0.05):
        """Get candidates for linking — exclude self, prefer same batch."""
        start_date = date - timedelta(days=3)
        end_date = date + timedelta(days=3)
        
        # First, try same batch
        candidates = self.session.query(FinexaTransaction).filter(
            FinexaTransaction.id != new_tx_id,
            FinexaTransaction.linked_id.is_(None),
            FinexaTransaction.batch_id == batch_id,  # ← SAME BATCH FIRST
            func.abs(FinexaTransaction.amount - amount) < amount * tolerance,
            FinexaTransaction.transaction_date.between(start_date, end_date)
        ).all()
        
        # If no same-batch candidates, try any batch
        if not candidates:
            candidates = self.session.query(FinexaTransaction).filter(
                FinexaTransaction.id != new_tx_id,
                FinexaTransaction.linked_id.is_(None),
                func.abs(FinexaTransaction.amount - amount) < amount * tolerance,
                FinexaTransaction.transaction_date.between(start_date, end_date)
            ).all()
        
        return candidates
    
    def link_transactions(self, id1, id2):
        """Link two transactions bidirectionally."""
        tx1 = self.get_transaction_by_id(id1)
        tx2 = self.get_transaction_by_id(id2)
        if tx1 and tx2:
            tx1.linked_id = id2
            tx2.linked_id = id1
            tx1.is_matched = True
            tx2.is_matched = True
            tx1.last_linked_at = datetime.utcnow()
            tx2.last_linked_at = datetime.utcnow()
            self.session.commit()
    
    def close(self):
        self.session.close()

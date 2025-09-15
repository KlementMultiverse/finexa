from sqlalchemy import create_engine, Column, Integer, String, Float, Date, Boolean, JSON, ForeignKey, TIMESTAMP
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
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
    document_type = Column(String(20), nullable=False)  # 'receipt' or 'statement_line'
    source_path = Column(String, nullable=False)
    raw_text = Column(String, nullable=False)
    agent_schema = Column(JSON, nullable=False)  # Dynamic fields
    linked_id = Column(Integer, ForeignKey('mission_transactions.id'), nullable=True)
    is_matched = Column(Boolean, default=False)  # Auto-calculated later
    batch_id = Column(String, nullable=False)  # UUID as string
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
    
    def get_unlinked_transactions(self, date, amount, tolerance=0.05):
        """Get candidates for linking"""
        from sqlalchemy import and_, func
        return self.session.query(FinexaTransaction).filter(
            FinexaTransaction.id != kwargs.get('id'),
            FinexaTransaction.linked_id.is_(None),
            func.abs(FinexaTransaction.amount - amount) < amount * tolerance,
            FinexaTransaction.transaction_date.between(
                date.replace(day=1),  # Start of month
                date.replace(day=28) + timedelta(days=4)  # End of month (approx)
            )
        ).all()
    
    def link_transactions(self, id1, id2):
        """Link two transactions bidirectionally"""
        tx1 = self.session.query(FinexaTransaction).filter_by(id=id1).first()
        tx2 = self.session.query(FinexaTransaction).filter_by(id=id2).first()
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

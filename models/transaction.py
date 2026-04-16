from . import db
from utils import get_canary_time

class VacationTransaction(db.Model):
    __tablename__ = 'vacation_transactions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    year = db.Column(db.Integer, nullable=False)
    days = db.Column(db.Integer, nullable=False)  # Puede ser positivo o negativo
    transaction_type = db.Column(db.String(50), nullable=False) # 'initial_migration', 'base', 'consumed', 'adjustment', 'carryover'
    description = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=get_canary_time, nullable=False)
    
    def __repr__(self):
        return f'<Transaction {self.days} days for User {self.user_id} ({self.year})>'
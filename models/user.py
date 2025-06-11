from . import db
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import date
from utils import get_canary_time

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id'), nullable=False)
    role = db.Column(db.String(20), default='employee', nullable=False)  # 'admin' o 'employee'
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=get_canary_time, nullable=False)
    
    # Relaciones
    requests = db.relationship('Request', foreign_keys='Request.user_id', backref='user', lazy=True, cascade='all, delete-orphan')
    worked_holidays = db.relationship('WorkedHoliday', foreign_keys='WorkedHoliday.user_id', backref='user', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<User {self.email}>'
    
    def set_password(self, password):
        """Establecer contraseña hasheada"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Verificar contraseña"""
        return check_password_hash(self.password_hash, password)
    
    def is_admin(self):
        """Verificar si el usuario es administrador"""
        return self.role == 'admin'
    
    def has_pending_requests(self):
        """Verificar si el usuario tiene solicitudes pendientes"""
        from .request import Request
        return Request.query.filter_by(user_id=self.id, status='pending').first() is not None
    
    def get_pending_requests(self):
        """Obtener todas las solicitudes pendientes del usuario"""
        from .request import Request
        return Request.query.filter_by(user_id=self.id, status='pending').all()
    
    def get_vacation_requests(self, year=None):
        """Obtener solicitudes de vacaciones del usuario"""
        from .request import Request
        
        query = Request.query.filter_by(user_id=self.id, type='vacation')
        
        if year:
            query = query.filter(db.extract('year', Request.start_date) == year)
        
        return query.order_by(Request.created_at.desc()).all()
    
    def get_recovery_requests(self, year=None):
        """Obtener solicitudes de recuperación del usuario"""
        from .request import Request
        
        query = Request.query.filter_by(user_id=self.id, type='recovery')
        
        if year:
            query = query.filter(db.extract('year', Request.start_date) == year)
        
        return query.order_by(Request.created_at.desc()).all()
    
    def get_worked_holidays(self, year=None):
        """Obtener festivos trabajados por el usuario"""
        from .holiday import WorkedHoliday
        
        query = WorkedHoliday.query.filter_by(user_id=self.id)
        
        if year:
            query = query.filter(db.extract('year', WorkedHoliday.date) == year)
        
        return query.order_by(WorkedHoliday.date.desc()).all()
    
    def is_on_vacation(self, check_date=None):
        """Verificar si el usuario está de vacaciones en una fecha específica"""
        from .request import Request
        
        if not check_date:
            check_date = date.today()
        
        vacation_request = Request.query.filter(
            Request.user_id == self.id,
            Request.type == 'vacation',
            Request.status == 'approved',
            Request.start_date <= check_date,
            Request.end_date >= check_date
        ).first()
        
        return vacation_request is not None
    
    def get_vacation_days_used(self, year=None):
        """Calcular días de vacaciones utilizados"""
        from .request import Request
        from utils import calculate_vacation_days
        
        if not year:
            year = get_canary_time().year
        
        approved_requests = Request.query.filter(
            Request.user_id == self.id,
            Request.type == 'vacation',
            Request.status == 'approved',
            db.extract('year', Request.start_date) == year
        ).all()
        
        total_days = 0
        for request in approved_requests:
            total_days += calculate_vacation_days(request.start_date, request.end_date)
        
        return total_days
    
    def get_notifications_count(self):
        """Obtener número de notificaciones no leídas"""
        from .notification import Notification
        return Notification.get_unread_count_for_user(self.id)
    
    def get_recent_notifications(self, limit=10):
        """Obtener notificaciones recientes"""
        from .notification import Notification
        return Notification.get_recent_for_user(self.id, limit)
    
    def mark_all_notifications_read(self):
        """Marcar todas las notificaciones como leídas"""
        from .notification import Notification
        return Notification.mark_all_as_read_for_user(self.id)
    
    def has_overlapping_requests(self, start_date, end_date, exclude_request_id=None):
        """Verificar si el usuario tiene solicitudes que se solapan con las fechas dadas"""
        from .request import Request
        
        query = Request.query.filter(
            Request.user_id == self.id,
            Request.status.in_(['pending', 'approved']),
            Request.start_date <= end_date,
            Request.end_date >= start_date
        )
        
        if exclude_request_id:
            query = query.filter(Request.id != exclude_request_id)
        
        return query.first() is not None
    
    def can_request_vacation(self, start_date, end_date, exclude_request_id=None):
        """Verificar si el usuario puede solicitar vacaciones"""
        # Verificar solapamiento de fechas en lugar de solicitudes pendientes
        if self.has_overlapping_requests(start_date, end_date, exclude_request_id):
            return False, "Ya tienes una solicitud para fechas que se solapan con estas."
        
        # Verificar disponibilidad en el departamento
        if not self.department.can_approve_vacation(start_date, end_date, self.id):
            return False, f"Ya hay {self.department.max_concurrent_vacations} empleado(s) de vacaciones en esas fechas."
        
        return True, ""
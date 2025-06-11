from . import db
from datetime import date

class Department(db.Model):
    __tablename__ = 'departments'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    max_concurrent_vacations = db.Column(db.Integer, default=1, nullable=False)
    
    # Relaciones
    users = db.relationship('User', backref='department', lazy=True)
    
    def __repr__(self):
        return f'<Department {self.name}>'
    
    def get_employees(self):
        """Obtener todos los empleados del departamento"""
        return [user for user in self.users if user.role == 'employee' and user.is_active]
    
    def get_employees_on_vacation(self, start_date=None, end_date=None):
        """Obtener empleados que están de vacaciones en un rango de fechas"""
        from .request import Request
        
        if not start_date:
            start_date = date.today()
        if not end_date:
            end_date = start_date
            
        # Buscar solicitudes de vacaciones aprobadas que se solapen con el rango
        vacation_requests = Request.query.filter(
            Request.user_id.in_([user.id for user in self.get_employees()]),
            Request.type == 'vacation',
            Request.status == 'approved',
            Request.start_date <= end_date,
            Request.end_date >= start_date
        ).all()
        
        # Obtener los usuarios únicos
        users_on_vacation = []
        for request in vacation_requests:
            if request.user not in users_on_vacation:
                users_on_vacation.append(request.user)
                
        return users_on_vacation
    
    def can_approve_vacation(self, start_date, end_date, exclude_user_id=None):
        """Verificar si se puede aprobar una nueva solicitud de vacaciones"""
        employees_on_vacation = self.get_employees_on_vacation(start_date, end_date)
        
        # Excluir el usuario que está solicitando (para ediciones)
        if exclude_user_id:
            employees_on_vacation = [user for user in employees_on_vacation 
                                   if user.id != exclude_user_id]
        
        return len(employees_on_vacation) < self.max_concurrent_vacations
    
    def get_available_employees_for_vacation(self, start_date, end_date):
        """Obtener empleados disponibles para vacaciones en un rango de fechas"""
        all_employees = self.get_employees()
        employees_on_vacation = self.get_employees_on_vacation(start_date, end_date)
        
        available = []
        for employee in all_employees:
            if employee not in employees_on_vacation:
                available.append(employee)
                
        return available
    
    def get_vacation_stats(self):
        """Obtener estadísticas de vacaciones del departamento"""
        from .request import Request
        from utils import get_canary_time
        
        current_year = get_canary_time().year
        
        total_requests = Request.query.filter(
            Request.user_id.in_([user.id for user in self.get_employees()]),
            Request.type == 'vacation',
            db.extract('year', Request.created_at) == current_year
        ).count()
        
        approved_requests = Request.query.filter(
            Request.user_id.in_([user.id for user in self.get_employees()]),
            Request.type == 'vacation',
            Request.status == 'approved',
            db.extract('year', Request.created_at) == current_year
        ).count()
        
        pending_requests = Request.query.filter(
            Request.user_id.in_([user.id for user in self.get_employees()]),
            Request.type == 'vacation',
            Request.status == 'pending',
            db.extract('year', Request.created_at) == current_year
        ).count()
        
        return {
            'total_requests': total_requests,
            'approved_requests': approved_requests,
            'pending_requests': pending_requests,
            'employees_count': len(self.get_employees())
        }
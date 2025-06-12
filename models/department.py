from . import db
from datetime import date

class Department(db.Model):
    __tablename__ = 'departments'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    max_concurrent_vacations = db.Column(db.Integer, default=1, nullable=False)
    
    # NUEVO: Días de vacaciones por año para empleados de este departamento
    vacation_days_per_year = db.Column(db.Integer, default=22, nullable=False)
    
    # NUEVO: Campos de auditoría
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp(), nullable=False)
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())
    
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
    
    # ============================================================================
    # NUEVOS MÉTODOS PARA GESTIÓN
    # ============================================================================
    
    def update_details(self, name=None, max_concurrent=None, vacation_days=None):
        """Actualizar detalles del departamento"""
        if name and name != self.name:
            # Verificar que no exista otro departamento con ese nombre
            existing = Department.query.filter(
                Department.name == name,
                Department.id != self.id
            ).first()
            if existing:
                return False, "Ya existe un departamento con ese nombre"
            self.name = name
        
        if max_concurrent is not None:
            if max_concurrent < 1:
                return False, "El máximo de vacaciones concurrentes debe ser al menos 1"
            self.max_concurrent_vacations = max_concurrent
        
        if vacation_days is not None:
            if vacation_days < 0:
                return False, "Los días de vacaciones no pueden ser negativos"
            if vacation_days > 50:
                return False, "Los días de vacaciones no pueden superar 50 por año"
            self.vacation_days_per_year = vacation_days
        
        try:
            db.session.commit()
            return True, "Departamento actualizado correctamente"
        except Exception as e:
            db.session.rollback()
            return False, f"Error al actualizar: {str(e)}"
    
    def can_be_deleted(self):
        """Verificar si el departamento puede ser eliminado"""
        active_employees = len(self.get_employees())
        if active_employees > 0:
            return False, f"No se puede eliminar: tiene {active_employees} empleado(s) activo(s)"
        
        # Verificar si hay solicitudes asociadas
        from .request import Request
        requests_count = Request.query.filter(
            Request.user_id.in_([user.id for user in self.users])
        ).count()
        
        if requests_count > 0:
            return False, f"No se puede eliminar: tiene {requests_count} solicitud(es) asociada(s)"
        
        return True, "Se puede eliminar"
    
    def delete_department(self):
        """Eliminar departamento"""
        can_delete, message = self.can_be_deleted()
        if not can_delete:
            return False, message
        
        try:
            db.session.delete(self)
            db.session.commit()
            return True, "Departamento eliminado correctamente"
        except Exception as e:
            db.session.rollback()
            return False, f"Error al eliminar: {str(e)}"
    
    @staticmethod
    def create_department(name, max_concurrent=1, vacation_days=22):
        """Crear nuevo departamento"""
        # Verificar que no exista
        existing = Department.query.filter_by(name=name).first()
        if existing:
            return None, "Ya existe un departamento con ese nombre"
        
        # Validaciones
        if max_concurrent < 1:
            return None, "El máximo de vacaciones concurrentes debe ser al menos 1"
        
        if vacation_days < 0 or vacation_days > 50:
            return None, "Los días de vacaciones deben estar entre 0 y 50"
        
        try:
            department = Department(
                name=name,
                max_concurrent_vacations=max_concurrent,
                vacation_days_per_year=vacation_days
            )
            db.session.add(department)
            db.session.commit()
            return department, "Departamento creado correctamente"
        except Exception as e:
            db.session.rollback()
            return None, f"Error al crear: {str(e)}"
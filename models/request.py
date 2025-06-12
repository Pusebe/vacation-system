from . import db
from utils import get_canary_time, calculate_vacation_days, validate_date_range
from datetime import date

class Request(db.Model):
    __tablename__ = 'requests'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    type = db.Column(db.String(20), nullable=False)  # 'vacation' o 'recovery'
    status = db.Column(db.String(20), default='pending', nullable=False)  # 'pending', 'approved', 'rejected'
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    reason = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=get_canary_time, nullable=False)
    reviewed_at = db.Column(db.DateTime)
    reviewed_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    # 🆕 NUEVA COLUMNA: Relación con festivo trabajado (solo para recuperaciones)
    worked_holiday_id = db.Column(db.Integer, db.ForeignKey('worked_holidays.id'), nullable=True)
    
    # Relación con el revisor (sin backref para evitar conflictos)
    reviewer = db.relationship('User', foreign_keys=[reviewed_by])
    
    # 🆕 La relación worked_holiday se define en WorkedHoliday con backref
    
    def __repr__(self):
        return f'<Request {self.type} {self.user.name} {self.start_date}-{self.end_date}>'
    
    def validate(self):
        """Validar la solicitud antes de guardar"""
        errors = []
        
        # Validar rango de fechas
        from utils import validate_date_range
        is_valid, error_msg = validate_date_range(self.start_date, self.end_date)
        if not is_valid:
            errors.append(error_msg)
        
        # Validar tipo de solicitud
        if self.type not in ['vacation', 'recovery']:
            errors.append("Tipo de solicitud inválido.")
        
        # Obtener el usuario directamente desde la base de datos
        from . import User
        user = User.query.get(self.user_id)
        if not user:
            errors.append("Usuario no encontrado.")
            return errors
        
        # Validaciones específicas por tipo
        if self.type == 'vacation':
            can_request, error_msg = user.can_request_vacation(self.start_date, self.end_date, self.id)
            if not can_request:
                errors.append(error_msg)
        
        # Para recuperaciones, validar que sea solo 1 día
        elif self.type == 'recovery':
            if self.start_date != self.end_date:
                errors.append("Las recuperaciones solo pueden ser de 1 día.")
                
            if user.has_overlapping_requests(self.start_date, self.end_date, self.id):
                errors.append("Ya tienes una solicitud para fechas que se solapan con estas.")
                
            # Si tiene worked_holiday_id, verificar que el festivo esté disponible
            if self.worked_holiday_id:
                from .holiday import WorkedHoliday
                holiday = WorkedHoliday.query.get(self.worked_holiday_id)
                if holiday and holiday.user_id != self.user_id:
                    errors.append("No puedes usar un festivo de otro usuario.")
                if holiday and holiday.status != 'approved':
                    errors.append("Solo puedes usar festivos aprobados para recuperación.")
        
        return errors
    
    def calculate_days(self):
        """Calcular número de días de la solicitud"""
        return calculate_vacation_days(self.start_date, self.end_date)
    
    def approve(self, admin_user):
        """Aprobar la solicitud"""
        # Solo validar fechas básicas y disponibilidad de departamento para vacaciones
        if self.type == 'vacation':
            from . import User
            user = User.query.get(self.user_id)
            
            # Solo verificar disponibilidad del departamento, no solicitudes pendientes
            if not user.department.can_approve_vacation(self.start_date, self.end_date, self.user_id):
                # Obtener información específica de quién está de vacaciones
                employees_on_vacation = user.department.get_employees_on_vacation(self.start_date, self.end_date)
                employees_on_vacation = [emp for emp in employees_on_vacation if emp.id != self.user_id]
                
                if employees_on_vacation:
                    names = [emp.name for emp in employees_on_vacation]
                    names_str = ", ".join(names)
                    return False, [f"No se puede aprobar: {names_str} ya tiene(n) vacaciones en esas fechas. Máximo permitido en {user.department.name}: {user.department.max_concurrent_vacations} empleado(s)."]
                else:
                    return False, [f"No se puede aprobar: Ya hay {user.department.max_concurrent_vacations} empleado(s) de vacaciones en esas fechas en el departamento {user.department.name}."]
        
        self.status = 'approved'
        self.reviewed_at = get_canary_time()
        self.reviewed_by = admin_user.id
        
        try:
            db.session.commit()
            
            # Crear notificación para el usuario
            from .notification import Notification
            notification = Notification.create_for_user_request_response(self)
            db.session.add(notification)
            db.session.commit()
            
            return True, "Solicitud aprobada correctamente."
        except Exception as e:
            db.session.rollback()
            return False, [f"Error al aprobar la solicitud: {str(e)}"]
    
    def reject(self, admin_user, reason=None):
        """Rechazar la solicitud"""
        self.status = 'rejected'
        self.reviewed_at = get_canary_time()
        self.reviewed_by = admin_user.id
        
        if reason:
            self.reason = f"{self.reason or ''}\n\nMotivo del rechazo: {reason}".strip()
        
        try:
            db.session.commit()
            
            # Crear notificación para el usuario
            from .notification import Notification
            notification = Notification.create_for_user_request_response(self)
            db.session.add(notification)
            db.session.commit()
            
            return True, "Solicitud rechazada correctamente."
        except Exception as e:
            db.session.rollback()
            return False, f"Error al rechazar la solicitud: {str(e)}"
    
    def cancel(self):
        """Cancelar la solicitud (solo si está pendiente)"""
        if self.status != 'pending':
            return False, "Solo se pueden cancelar solicitudes pendientes."
        
        try:
            db.session.delete(self)
            db.session.commit()
            return True, "Solicitud cancelada correctamente."
        except Exception as e:
            db.session.rollback()
            return False, f"Error al cancelar la solicitud: {str(e)}"
    
    def can_be_cancelled(self):
        """Verificar si la solicitud puede ser cancelada por el usuario"""
        return self.status == 'pending'
    
    def can_be_modified(self):
        """Verificar si la solicitud puede ser modificada"""
        return self.status == 'pending' and self.start_date > date.today()
    
    def get_status_class(self):
        """Obtener clase CSS para el estado"""
        status_classes = {
            'pending': 'badge bg-warning',
            'approved': 'badge bg-success',
            'rejected': 'badge bg-danger'
        }
        return status_classes.get(self.status, 'badge bg-secondary')
    
    def get_status_text(self):
        """Obtener texto del estado en español"""
        status_text = {
            'pending': 'Pendiente',
            'approved': 'Aprobada',
            'rejected': 'Rechazada'
        }
        return status_text.get(self.status, 'Desconocido')
    
    def get_type_text(self):
        """Obtener texto del tipo en español"""
        type_text = {
            'vacation': 'Vacaciones',
            'recovery': 'Recuperación'
        }
        return type_text.get(self.type, 'Desconocido')
    
    def is_current(self):
        """Verificar si la solicitud está vigente actualmente"""
        if self.status != 'approved':
            return False
        
        today = date.today()
        return self.start_date <= today <= self.end_date
    
    def is_future(self):
        """Verificar si la solicitud es futura"""
        return self.start_date > date.today()
    
    def can_be_edited(self):
        """Solo admin puede editar cualquier solicitud"""
        return True  # El check de admin se hace en la vista
    
    def can_be_deleted(self):
        """Solo admin puede borrar cualquier solicitud"""
        return True  # El check de admin se hace en la vista
    
    def update(self, admin_user, **kwargs):
        """Actualizar solicitud (solo admin)"""
        old_values = {
            'start_date': self.start_date,
            'end_date': self.end_date,
            'type': self.type,
            'reason': self.reason,
            'status': self.status
        }
        
        # Actualizar campos
        for field, value in kwargs.items():
            if hasattr(self, field):
                setattr(self, field, value)
        
        # Si cambió fechas o tipo, revalidar
        if any(kwargs.get(field) != old_values[field] for field in ['start_date', 'end_date', 'type']):
            if self.status == 'approved' and self.type == 'vacation':
                # Validar disponibilidad del departamento con el cambio
                from . import User
                user = User.query.get(self.user_id)
                if not user.department.can_approve_vacation(self.start_date, self.end_date, self.user_id):
                    return False, f"Las nuevas fechas chocan con vacaciones en {user.department.name}"
        
        # Si cambió el estado, actualizar campos relacionados
        if 'status' in kwargs and kwargs['status'] != old_values['status']:
            if kwargs['status'] in ['approved', 'rejected']:
                self.reviewed_at = get_canary_time()
                self.reviewed_by = admin_user.id
            elif kwargs['status'] == 'pending':
                self.reviewed_at = None
                self.reviewed_by = None
        
        try:
            db.session.commit()
            return True, "Solicitud actualizada correctamente."
        except Exception as e:
            db.session.rollback()
            return False, f"Error al actualizar: {str(e)}"
    
    def delete(self):
        """Borrar solicitud (solo admin)"""
        try:
            db.session.delete(self)
            db.session.commit()
            return True, "Solicitud eliminada correctamente."
        except Exception as e:
            db.session.rollback()
            return False, f"Error al eliminar: {str(e)}"
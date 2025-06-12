from . import db
from utils import get_canary_time
from datetime import date

class WorkedHoliday(db.Model):
    __tablename__ = 'worked_holidays'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(20), default='pending', nullable=False)  # 'pending', 'approved'
    description = db.Column(db.String(255))  # Descripción del festivo trabajado
    approved_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=get_canary_time, nullable=False)
    approved_at = db.Column(db.DateTime)
    
    # Relación con el aprobador (sin backref para evitar conflictos)
    approver = db.relationship('User', foreign_keys=[approved_by])
    
    # 🆕 NUEVA RELACIÓN: Un festivo puede tener muchas solicitudes de recuperación
    recovery_requests = db.relationship('Request', 
                                      foreign_keys='Request.worked_holiday_id',
                                      backref='worked_holiday', 
                                      lazy=True,
                                      cascade='all, delete-orphan')
    
    # Constraint para evitar duplicados
    __table_args__ = (db.UniqueConstraint('user_id', 'date', name='unique_user_holiday'),)
    
    def __repr__(self):
        return f'<WorkedHoliday {self.user.name} {self.date}>'
    
    def validate(self):
        """Validar el festivo trabajado"""
        errors = []
        
        # Verificar que la fecha no sea futura
        if self.date > date.today():
            errors.append("No puedes marcar como trabajado un festivo futuro.")
        
        # Verificar que no sea muy antiguo (máximo 1 año)
        from datetime import timedelta
        max_past_date = date.today() - timedelta(days=365)
        if self.date < max_past_date:
            errors.append("No puedes marcar festivos trabajados de hace más de un año.")
        
        # Verificar que no esté duplicado
        existing = WorkedHoliday.query.filter(
            WorkedHoliday.user_id == self.user_id,
            WorkedHoliday.date == self.date,
            WorkedHoliday.id != self.id
        ).first()
        
        if existing:
            errors.append("Ya has marcado este festivo como trabajado.")
        
        return errors
    
    def approve(self, admin_user):
        """Aprobar el festivo trabajado"""
        if self.status == 'approved':
            return False, "Este festivo ya está aprobado."
        
        if self.status == 'rejected':
            return False, "Este festivo fue rechazado y no se puede aprobar."
        
        self.status = 'approved'
        self.approved_at = get_canary_time()
        self.approved_by = admin_user.id
        
        try:
            db.session.commit()
            
            # Crear notificación para el usuario
            from .notification import Notification
            notification = Notification.create_for_user_holiday_response(self)
            db.session.add(notification)
            db.session.commit()
            
            return True, "Festivo aprobado correctamente."
        except Exception as e:
            db.session.rollback()
            return False, f"Error al aprobar el festivo: {str(e)}"
    
    def reject(self, admin_user, reason=None):
        """Rechazar el festivo trabajado"""
        if self.status == 'approved':
            return False, "Este festivo ya está aprobado y no se puede rechazar."
        
        if self.status == 'rejected':
            return False, "Este festivo ya está rechazado."
        
        self.status = 'rejected'
        self.approved_at = get_canary_time()
        self.approved_by = admin_user.id
        
        if reason:
            self.description = f"{self.description or ''}\n\nMotivo del rechazo: {reason}".strip()
        
        try:
            db.session.commit()
            
            # Crear notificación para el usuario
            from .notification import Notification
            notification = Notification.create_for_user_holiday_rejection(self)
            db.session.add(notification)
            db.session.commit()
            
            return True, "Festivo rechazado correctamente."
        except Exception as e:
            db.session.rollback()
            return False, f"Error al rechazar el festivo: {str(e)}"
    
    def can_be_cancelled(self):
        """Verificar si el festivo puede ser cancelado por el usuario"""
        return self.status == 'pending'
    
    def cancel(self):
        """Cancelar el festivo trabajado (solo si está pendiente)"""
        if self.status != 'pending':
            return False, "Solo se pueden cancelar festivos pendientes."
        
        try:
            db.session.delete(self)
            db.session.commit()
            return True, "Festivo cancelado correctamente."
        except Exception as e:
            db.session.rollback()
            return False, f"Error al cancelar el festivo: {str(e)}"
    
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
            'pending': 'En revisión',
            'approved': 'Aprobado',
            'rejected': 'Rechazado'
        }
        return status_text.get(self.status, 'Desconocido')
    
    # En models/holiday.py - Reemplazar el método is_available_for_recovery():
    def is_available_for_recovery(self):
        """Verificar si está disponible para recuperación"""
        if self.status != 'approved':
            return False, "El festivo debe estar aprobado para solicitar recuperación."
        
        # Usar la relación directa en lugar de buscar por texto
        recovery_status, recovery_request = self.get_recovery_status()
        
        if recovery_status == 'approved':
            return False, "Este festivo ya ha sido usado para una recuperación aprobada."
        elif recovery_status == 'pending':
            return False, "Ya tienes una recuperación pendiente para este festivo."
        # Si recovery_status == 'rejected' o None, está disponible
        else:
            return True, "Disponible para recuperación"

        def has_pending_or_approved_recovery(self):
            """Verificar si tiene recuperación o está completado"""
            recovery_status, _ = self.get_recovery_status()
            return recovery_status is not None
# En models/holiday.py - Reemplazar el método get_recovery_status():

# REEMPLAZAR temporalmente en models/holiday.py

    def get_recovery_status(self):
        """Obtener el estado de la recuperación usando la relación directa"""
        # ✅ USAR LA RELACIÓN DIRECTA
        active_recovery = None
        for request in self.recovery_requests:
            if request.status in ['pending', 'approved']:
                active_recovery = request
                break
        
        if active_recovery:
            return active_recovery.status, active_recovery
        
        return None, None

    def create_recovery_request(self, recovery_date, reason=None):
        """Crear una solicitud de recuperación usando este festivo"""
        from .request import Request
        
        # Verificar disponibilidad
        is_available, message = self.is_available_for_recovery()
        if not is_available:
            return None, message
        
        # ✅ CREAR REQUEST CON worked_holiday_id CORRECTO
        recovery_request = Request(
            user_id=self.user_id,
            type='recovery',
            start_date=recovery_date,
            end_date=recovery_date,
            worked_holiday_id=self.id,  # 🎯 ESTO ES CLAVE
            reason=f"Recuperación por festivo trabajado el {self.date}: {self.description or 'Sin descripción'}"
        )
        
        if reason:
            recovery_request.reason += f"\n\nMotivo adicional: {reason}"
        
        return recovery_request, "Solicitud de recuperación creada."
        
    @staticmethod
    def get_common_holidays():
        """Obtener lista de festivos comunes en España/Canarias"""
        current_year = get_canary_time().year
        
        # Festivos fijos comunes
        common_holidays = [
            f"Año Nuevo ({current_year}-01-01)",
            f"Reyes Magos ({current_year}-01-06)",
            f"Día del Trabajador ({current_year}-05-01)",
            f"Asunción ({current_year}-08-15)",
            f"Fiesta Nacional ({current_year}-10-12)",
            f"Todos los Santos ({current_year}-11-01)",
            f"Constitución ({current_year}-12-06)",
            f"Inmaculada ({current_year}-12-08)",
            f"Navidad ({current_year}-12-25)",
            f"Día de Canarias ({current_year}-05-30)",
        ]
        
        return common_holidays
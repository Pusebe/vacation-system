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
    vacation_days_override = db.Column(db.Integer, nullable=True)  # Override personalizado de días
    hire_date = db.Column(db.Date, nullable=True)  # Fecha de contratación
    updated_at = db.Column(db.DateTime, default=get_canary_time, onupdate=get_canary_time)
    
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

    def get_available_holidays_count(self):
        """Obtener número de festivos aprobados disponibles para recuperación"""
        from .holiday import WorkedHoliday
        
        approved_holidays = WorkedHoliday.query.filter_by(
            user_id=self.id, 
            status='approved'
        ).all()
        
        available_count = 0
        for holiday in approved_holidays:
            # Verificar si ya tiene recuperación asociada
            recovery_status, _ = holiday.get_recovery_status()
            if not recovery_status:  # No tiene recuperación
                available_count += 1
        
        return available_count

    def get_pending_approvals_count(self):
        """Obtener número de solicitudes y festivos pendientes de aprobación"""
        from .request import Request
        from .holiday import WorkedHoliday
        
        pending_requests = Request.query.filter_by(user_id=self.id, status='pending').count()
        pending_holidays = WorkedHoliday.query.filter_by(user_id=self.id, status='pending').count()
        
        return pending_requests + pending_holidays

    def use_available_holiday(self):
        """Marcar un festivo disponible como usado (para recuperaciones de admin)"""
        from .holiday import WorkedHoliday
        
        # Buscar el primer festivo aprobado sin recuperación
        approved_holidays = WorkedHoliday.query.filter_by(
            user_id=self.id, 
            status='approved'
        ).all()
        
        for holiday in approved_holidays:
            recovery_status, _ = holiday.get_recovery_status()
            if not recovery_status:  # Festivo disponible
                # Marcar como usado añadiendo una nota
                if holiday.description:
                    holiday.description += " [USADO PARA RECUPERACIÓN]"
                else:
                    holiday.description = "[USADO PARA RECUPERACIÓN]"
                
                return holiday
        
        return None

    def get_vacation_days_base(self, year=None):
        """Obtener días BASE del departamento o override (SIN proporcional)"""
        if self.vacation_days_override is not None:
            return self.vacation_days_override
        return self.department.vacation_days_per_year

    def get_vacation_days_per_year(self, year=None):
        """Obtener días de vacaciones por año (con cálculo proporcional si aplica)"""
        if not year:
            year = get_canary_time().year
            
        # Si tiene override personalizado, usarlo tal cual (sin proporcional)
        if self.vacation_days_override is not None:
            return self.vacation_days_override
        
        # Si no tiene override, usar días del departamento con cálculo proporcional
        base_days = self.department.vacation_days_per_year
        
        # Si no tiene fecha de contratación, devolver días completos
        if not self.hire_date:
            return base_days
        
        # Si fue contratado antes del año en cuestión, días completos
        if self.hire_date.year < year:
            return base_days
        
        # Si fue contratado en el año en cuestión, calcular proporcionalmente
        if self.hire_date.year == year:
            start_of_year = date(year, 1, 1)
            end_of_year = date(year, 12, 31)
            
            days_worked = (end_of_year - self.hire_date).days + 1
            total_days_year = (end_of_year - start_of_year).days + 1
            
            proportion = days_worked / total_days_year
            proportional_days = round(base_days * proportion)
            
            return proportional_days
        
        # Si fue contratado después del año en cuestión, 0 días
        return 0

    def get_vacation_days_available(self, year=None):
        """Calcular días de vacaciones disponibles incluyendo arrastre completo del año anterior"""
        if not year:
            year = get_canary_time().year
        
        # Días base del año actual (con proporcional si aplica)
        vacation_days_total = self.get_vacation_days_per_year(year)
        vacation_days_used = self.get_vacation_days_used(year)
        
        # Calcular días no usados del año anterior (sin límites)
        carryover_days = 0
        if year > 2024:  # Cambiado a 2024 para testing - cambiar a 2025 en producción
            previous_year = year - 1
            previous_total = self.get_vacation_days_per_year(previous_year)
            previous_used = self.get_vacation_days_used(previous_year)
            previous_unused = previous_total - previous_used
            
            # Arrastrar TODOS los días no usados (pueden ser muchos)
            if previous_unused > 0:
                carryover_days = previous_unused
        
        total_available = vacation_days_total + carryover_days
        return total_available - vacation_days_used

    def is_vacation_balance_negative(self, year=None):
        """Verificar si el balance de vacaciones está en negativo"""
        return self.get_vacation_days_available(year) < 0

    def get_vacation_balance_info(self, year=None):
        """Obtener información completa del balance de vacaciones incluyendo arrastre"""
        if not year:
            year = get_canary_time().year
        
        # Días base del año
        base_days = self.get_vacation_days_per_year(year)
        used_days = self.get_vacation_days_used(year)
        
        # Calcular arrastre del año anterior
        carryover_days = 0
        if year > 2024:  # Cambiado a 2024 para testing
            previous_year = year - 1
            previous_total = self.get_vacation_days_per_year(previous_year)
            previous_used = self.get_vacation_days_used(previous_year)
            previous_unused = previous_total - previous_used
            
            if previous_unused > 0:
                carryover_days = previous_unused
        
        total_days = base_days + carryover_days
        available_days = total_days - used_days
        
        return {
            'base_days': base_days,
            'carryover_days': carryover_days,
            'total_days': total_days,
            'used_days': used_days,
            'available_days': available_days,
            'is_negative': available_days < 0,
            'year': year,
            'is_proportional': self.hire_date and self.hire_date.year == year and not self.vacation_days_override,
            'hire_date': self.hire_date
        }

    def would_exceed_vacation_days(self, start_date, end_date, year=None):
        """Verificar si una solicitud excedería los días disponibles"""
        if not year:
            year = start_date.year if start_date else get_canary_time().year
        
        from utils import calculate_vacation_days
        requested_days = calculate_vacation_days(start_date, end_date)
        available_days = self.get_vacation_days_available(year)
        
        if requested_days > available_days:
            excess_days = requested_days - available_days
            return True, excess_days, {
                'requested_days': requested_days,
                'available_days': available_days,
                'would_have_after': available_days - requested_days
            }
        
        return False, 0, {
            'requested_days': requested_days,
            'available_days': available_days,
            'would_have_after': available_days - requested_days
        }

    def update_profile(self, name=None, email=None, department_id=None, role=None, 
                      vacation_days_override=None, hire_date=None, is_active=None):
        """Actualizar perfil de usuario (solo admin)"""
        errors = []
        
        if email and email != self.email:
            # Verificar que el email no esté en uso
            existing = User.query.filter(
                User.email == email,
                User.id != self.id
            ).first()
            if existing:
                errors.append("Ya existe un usuario con ese email")
            else:
                self.email = email
        
        if name:
            self.name = name
        
        if department_id:
            from .department import Department
            department = Department.query.get(department_id)
            if not department:
                errors.append("Departamento no encontrado")
            else:
                self.department_id = department_id
        
        if role and role in ['admin', 'employee']:
            self.role = role
        
        if vacation_days_override is not None:
            if vacation_days_override < 0:
                errors.append("Los días de vacaciones no pueden ser negativos")
            elif vacation_days_override > 50:
                errors.append("Los días de vacaciones no pueden superar 50")
            else:
                self.vacation_days_override = vacation_days_override
        
        if hire_date:
            self.hire_date = hire_date
        
        if is_active is not None:
            self.is_active = is_active
        
        if errors:
            return False, errors
        
        try:
            db.session.commit()
            return True, ["Usuario actualizado correctamente"]
        except Exception as e:
            db.session.rollback()
            return False, [f"Error al actualizar: {str(e)}"]

    def can_be_deleted(self):
        """Verificar si el usuario puede ser eliminado"""
        # No eliminar si es el único admin
        if self.is_admin():
            admin_count = User.query.filter_by(role='admin', is_active=True).count()
            if admin_count <= 1:
                return False, "No se puede eliminar: es el único administrador activo"
        
        # Verificar solicitudes activas
        from .request import Request
        active_requests = Request.query.filter(
            Request.user_id == self.id,
            Request.status.in_(['pending', 'approved'])
        ).count()
        
        if active_requests > 0:
            return False, f"No se puede eliminar: tiene {active_requests} solicitud(es) activa(s)"
        
        return True, "Se puede eliminar"

    def deactivate_user(self):
        """Desactivar usuario en lugar de eliminarlo"""
        can_delete, message = self.can_be_deleted()
        if not can_delete:
            return False, message.replace("eliminar", "desactivar")
        
        try:
            self.is_active = False
            db.session.commit()
            return True, "Usuario desactivado correctamente"
        except Exception as e:
            db.session.rollback()
            return False, f"Error al desactivar: {str(e)}"

    @staticmethod
    def create_employee(name, email, department_id, password="temp123", 
                       role='employee', vacation_days_override=None, hire_date=None):
        """Crear nuevo empleado"""
        # Verificaciones
        if User.query.filter_by(email=email).first():
            return None, "Ya existe un usuario con ese email"
        
        from .department import Department
        department = Department.query.get(department_id)
        if not department:
            return None, "Departamento no encontrado"
        
        if vacation_days_override is not None and (vacation_days_override < 0 or vacation_days_override > 50):
            return None, "Los días de vacaciones deben estar entre 0 y 50"
        
        try:
            user = User(
                name=name,
                email=email,
                department_id=department_id,
                role=role,
                vacation_days_override=vacation_days_override,
                hire_date=hire_date or date.today(),
                is_active=True
            )
            user.set_password(password)
            
            db.session.add(user)
            db.session.commit()
            return user, "Usuario creado correctamente"
        except Exception as e:
            db.session.rollback()
            return None, f"Error al crear: {str(e)}"
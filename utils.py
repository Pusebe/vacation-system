from functools import wraps
from flask import session, redirect, url_for, flash
from datetime import datetime
import pytz

def login_required(f):
    """Decorador para rutas que requieren autenticación"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Debes iniciar sesión para acceder a esta página.', 'warning')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    """Decorador para rutas que requieren permisos de administrador"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Debes iniciar sesión para acceder a esta página.', 'warning')
            return redirect(url_for('auth.login'))
        
        if session.get('user_role') != 'admin':
            flash('No tienes permisos para acceder a esta página.', 'error')
            return redirect(url_for('dashboard.index'))
        
        return f(*args, **kwargs)
    return decorated_function

def get_canary_time():
    """Obtener la hora actual en zona horaria de Canarias"""
    canary_tz = pytz.timezone('Atlantic/Canary')
    return datetime.now(canary_tz)

def format_date(date_obj, format_str='%d/%m/%Y'):
    """Formatear fecha según zona horaria de Canarias"""
    if not date_obj:
        return ''
    
    if date_obj.tzinfo is None:
        # Si no tiene timezone, asumimos que es UTC y convertimos a Canarias
        utc_date = pytz.utc.localize(date_obj)
        canary_tz = pytz.timezone('Atlantic/Canary')
        canary_date = utc_date.astimezone(canary_tz)
        return canary_date.strftime(format_str)
    
    return date_obj.strftime(format_str)

def format_datetime(datetime_obj, format_str='%d/%m/%Y %H:%M'):
    """Formatear fecha y hora según zona horaria de Canarias"""
    return format_date(datetime_obj, format_str)

def is_weekend(date_obj):
    """Verificar si una fecha es fin de semana"""
    return date_obj.weekday() >= 5  # 5=Sábado, 6=Domingo

def calculate_vacation_days(start_date, end_date):
    """Calcular días de vacaciones incluyendo fines de semana"""
    if start_date > end_date:
        return 0
    
    delta = end_date - start_date
    return delta.days + 1  # +1 porque incluye ambos días

def validate_date_range(start_date, end_date):
    """Validar que el rango de fechas sea válido"""
    if start_date > end_date:
        return False, "La fecha de inicio no puede ser posterior a la fecha de fin."
    
    if start_date < get_canary_time().date():
        return False, "No puedes solicitar vacaciones para fechas pasadas."
    
    return True, ""

def create_notifications_for_new_request(request_obj):
    """Crear notificaciones para una nueva solicitud"""
    from models.notification import Notification
    from models import db
    
    try:
        # Crear notificaciones para administradores
        admin_notifications = Notification.create_for_admin_request(request_obj)
        for notification in admin_notifications:
            db.session.add(notification)
        
        db.session.commit()
        return True
    except Exception as e:
        db.session.rollback()
        return False

def create_notifications_for_new_holiday(holiday_obj):
    """Crear notificaciones para un nuevo festivo trabajado"""
    from models.notification import Notification
    from models import db
    
    try:
        # Crear notificaciones para administradores
        admin_notifications = Notification.create_for_admin_holiday(holiday_obj)
        for notification in admin_notifications:
            db.session.add(notification)
        
        db.session.commit()
        return True
    except Exception as e:
        db.session.rollback()
        return False
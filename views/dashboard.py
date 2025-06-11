from flask import Blueprint, render_template, g
from utils import login_required
from models import Request, WorkedHoliday, Department, User
from datetime import date, timedelta

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/')
@dashboard_bp.route('/dashboard')
@login_required
def index():
    """Dashboard principal - diferente contenido según rol"""
    if g.user.is_admin():
        return render_admin_dashboard()
    else:
        return render_employee_dashboard()

def render_admin_dashboard():
    """Dashboard para administradores"""
    # Estadísticas generales
    total_employees = User.query.filter_by(role='employee', is_active=True).count()
    pending_requests = Request.query.filter_by(status='pending').count()
    pending_holidays = WorkedHoliday.query.filter_by(status='pending').count()
    
    # Solicitudes recientes
    recent_requests = Request.query.filter_by(status='pending')\
                                  .order_by(Request.created_at.desc())\
                                  .limit(5).all()
    
    # Festivos pendientes
    recent_holidays = WorkedHoliday.query.filter_by(status='pending')\
                                        .order_by(WorkedHoliday.created_at.desc())\
                                        .limit(5).all()
    
    # Empleados actualmente de vacaciones
    today = date.today()
    current_vacations = Request.query.filter(
        Request.type == 'vacation',
        Request.status == 'approved',
        Request.start_date <= today,
        Request.end_date >= today
    ).all()
    
    # Resumen de empleados con sus días pendientes
    employees_summary = []
    all_employees = User.query.filter_by(role='employee', is_active=True).all()
    
    for employee in all_employees:
        # Calcular días de vacaciones disponibles (asumiendo 22 días por año)
        current_year = today.year
        vacation_days_used = employee.get_vacation_days_used(current_year)
        vacation_days_available = max(0, 22 - vacation_days_used)  # 22 días estándar
        
        # Calcular festivos aprobados disponibles para recuperación
        approved_holidays = WorkedHoliday.query.filter(
            WorkedHoliday.user_id == employee.id,
            WorkedHoliday.status == 'approved'
        ).all()
        
        holidays_to_recover = 0
        for holiday in approved_holidays:
            recovery_status, _ = holiday.get_recovery_status()
            if not recovery_status:  # No tiene recuperación asociada
                holidays_to_recover += 1
        
        # Estado actual del empleado
        is_on_vacation = employee.is_on_vacation(today)
        has_pending_requests = Request.query.filter_by(
            user_id=employee.id, 
            status='pending'
        ).first() is not None
        
        employees_summary.append({
            'employee': employee,
            'vacation_days_available': vacation_days_available,
            'holidays_to_recover': holidays_to_recover,
            'is_on_vacation': is_on_vacation,
            'has_pending_requests': has_pending_requests
        })
    
    return render_template('dashboard.html',
                         is_admin=True,
                         total_employees=total_employees,
                         pending_requests=pending_requests,
                         pending_holidays=pending_holidays,
                         recent_requests=recent_requests,
                         recent_holidays=recent_holidays,
                         current_vacations=current_vacations,
                         employees_summary=employees_summary)

def render_employee_dashboard():
    """Dashboard para empleados"""
    # Mis solicitudes recientes
    my_requests = Request.query.filter_by(user_id=g.user.id)\
                              .order_by(Request.created_at.desc())\
                              .limit(10).all()
    
    # Mis festivos trabajados
    my_holidays = WorkedHoliday.query.filter_by(user_id=g.user.id)\
                                    .order_by(WorkedHoliday.date.desc())\
                                    .limit(10).all()
    
    # Estado actual
    today = date.today()
    current_vacation = Request.query.filter(
        Request.user_id == g.user.id,
        Request.type == 'vacation',
        Request.status == 'approved',
        Request.start_date <= today,
        Request.end_date >= today
    ).first()
    
    # Próximas vacaciones
    next_vacation = Request.query.filter(
        Request.user_id == g.user.id,
        Request.type == 'vacation',
        Request.status == 'approved',
        Request.start_date > today
    ).order_by(Request.start_date.asc()).first()
    
    # Estadísticas del año
    current_year = today.year
    vacation_days_used = g.user.get_vacation_days_used(current_year)
    
    # Compañeros del departamento actualmente de vacaciones
    dept_vacations = g.user.department.get_employees_on_vacation(today, today)
    dept_vacations = [emp for emp in dept_vacations if emp.id != g.user.id]
    
    # Solicitudes pendientes de aprobación
    pending_requests = Request.query.filter_by(user_id=g.user.id, status='pending').count()
    pending_holidays = WorkedHoliday.query.filter_by(user_id=g.user.id, status='pending').count()
    
    # Festivos comunes para los modales
    common_holidays = WorkedHoliday.get_common_holidays()
    
    return render_template('dashboard.html',
                         is_admin=False,
                         my_requests=my_requests,
                         my_holidays=my_holidays,
                         current_vacation=current_vacation,
                         next_vacation=next_vacation,
                         vacation_days_used=vacation_days_used,
                         dept_vacations=dept_vacations,
                         pending_requests=pending_requests,
                         pending_holidays=pending_holidays,
                         common_holidays=common_holidays)
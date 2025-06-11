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
    
    # Estadísticas por departamento
    departments = Department.query.all()
    dept_stats = []
    for dept in departments:
        stats = dept.get_vacation_stats()
        employees_on_vacation = dept.get_employees_on_vacation(today, today)
        stats['employees_on_vacation'] = len(employees_on_vacation)
        stats['department'] = dept
        dept_stats.append(stats)
    
    return render_template('dashboard.html',
                         is_admin=True,
                         total_employees=total_employees,
                         pending_requests=pending_requests,
                         pending_holidays=pending_holidays,
                         recent_requests=recent_requests,
                         recent_holidays=recent_holidays,
                         current_vacations=current_vacations,
                         dept_stats=dept_stats)

def render_employee_dashboard():
    """Dashboard para empleados"""
    # Mis solicitudes recientes
    my_requests = Request.query.filter_by(user_id=g.user.id)\
                              .order_by(Request.created_at.desc())\
                              .limit(5).all()
    
    # Mis festivos trabajados
    my_holidays = WorkedHoliday.query.filter_by(user_id=g.user.id)\
                                    .order_by(WorkedHoliday.date.desc())\
                                    .limit(5).all()
    
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
    
    return render_template('dashboard.html',
                         is_admin=False,
                         my_requests=my_requests,
                         my_holidays=my_holidays,
                         current_vacation=current_vacation,
                         next_vacation=next_vacation,
                         vacation_days_used=vacation_days_used,
                         dept_vacations=dept_vacations,
                         pending_requests=pending_requests,
                         pending_holidays=pending_holidays)
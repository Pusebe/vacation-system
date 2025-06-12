from flask import Blueprint, render_template, request as flask_request, redirect, url_for, flash, g, jsonify
from utils import admin_required, get_canary_time
from models import db, User, Department
from datetime import datetime, date

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

# ============================================================================
# GESTIÓN DE DEPARTAMENTOS
# ============================================================================

@admin_bp.route('/departments')
@admin_required
def departments():
    """Lista de departamentos"""
    departments = Department.query.order_by(Department.name).all()
    return render_template('admin/departments.html', departments=departments)

@admin_bp.route('/departments', methods=['POST'])
@admin_required
def create_department():
    """Crear nuevo departamento"""
    try:
        name = flask_request.form.get('name', '').strip()
        max_concurrent = int(flask_request.form.get('max_concurrent_vacations', 1))
        vacation_days = int(flask_request.form.get('vacation_days_per_year', 22))
        
        if not name:
            flash('El nombre del departamento es obligatorio.', 'error')
            return redirect(url_for('admin.departments'))
        
        department, message = Department.create_department(name, max_concurrent, vacation_days)
        
        if department:
            flash(message, 'success')
        else:
            flash(message, 'error')
            
    except ValueError:
        flash('Error en los valores numéricos.', 'error')
    except Exception as e:
        flash(f'Error al crear departamento: {str(e)}', 'error')
    
    return redirect(url_for('admin.departments'))

@admin_bp.route('/departments/<int:dept_id>/edit', methods=['POST'])
@admin_required
def edit_department(dept_id):
    """Editar departamento"""
    department = Department.query.get_or_404(dept_id)
    
    try:
        name = flask_request.form.get('name', '').strip()
        max_concurrent = int(flask_request.form.get('max_concurrent_vacations'))
        vacation_days = int(flask_request.form.get('vacation_days_per_year'))
        
        success, message = department.update_details(
            name=name if name else None,
            max_concurrent=max_concurrent,
            vacation_days=vacation_days
        )
        
        if success:
            flash(message, 'success')
        else:
            flash(message, 'error')
            
    except ValueError:
        flash('Error en los valores numéricos.', 'error')
    except Exception as e:
        flash(f'Error al actualizar departamento: {str(e)}', 'error')
    
    return redirect(url_for('admin.departments'))

@admin_bp.route('/departments/<int:dept_id>/delete', methods=['POST'])
@admin_required
def delete_department(dept_id):
    """Eliminar departamento"""
    department = Department.query.get_or_404(dept_id)
    
    success, message = department.delete_department()
    
    if success:
        flash(message, 'success')
    else:
        flash(message, 'error')
    
    return redirect(url_for('admin.departments'))

# ============================================================================
# GESTIÓN DE EMPLEADOS
# ============================================================================

@admin_bp.route('/employees')
@admin_required
def employees():
    """Lista de empleados"""
    employees = User.query.filter_by(role='employee').order_by(User.name).all()
    departments = Department.query.order_by(Department.name).all()
    return render_template('admin/employees.html', employees=employees, departments=departments)

@admin_bp.route('/employees', methods=['POST'])
@admin_required
def create_employee():
    """Crear nuevo empleado"""
    try:
        name = flask_request.form.get('name', '').strip()
        email = flask_request.form.get('email', '').strip()
        department_id = int(flask_request.form.get('department_id'))
        password = flask_request.form.get('password', 'temp123')
        vacation_days_str = flask_request.form.get('vacation_days_override', '').strip()
        hire_date_str = flask_request.form.get('hire_date', '').strip()
        
        # Procesar valores opcionales
        vacation_days_override = None
        if vacation_days_str:
            vacation_days_override = int(vacation_days_str)
        
        hire_date = None
        if hire_date_str:
            hire_date = datetime.strptime(hire_date_str, '%Y-%m-%d').date()
        
        if not name or not email:
            flash('Nombre y email son obligatorios.', 'error')
            return redirect(url_for('admin.employees'))
        
        user, message = User.create_employee(
            name=name,
            email=email,
            department_id=department_id,
            password=password,
            vacation_days_override=vacation_days_override,
            hire_date=hire_date
        )
        
        if user:
            flash(f'{message} Contraseña temporal: {password}', 'success')
        else:
            flash(message, 'error')
            
    except ValueError as e:
        flash('Error en los valores introducidos.', 'error')
    except Exception as e:
        flash(f'Error al crear empleado: {str(e)}', 'error')
    
    return redirect(url_for('admin.employees'))

@admin_bp.route('/employees/<int:user_id>/edit', methods=['POST'])
@admin_required
def edit_employee(user_id):
    """Editar empleado"""
    user = User.query.get_or_404(user_id)
    
    try:
        name = flask_request.form.get('name', '').strip()
        email = flask_request.form.get('email', '').strip()
        department_id = int(flask_request.form.get('department_id'))
        vacation_days_str = flask_request.form.get('vacation_days_override', '').strip()
        hire_date_str = flask_request.form.get('hire_date', '').strip()
        is_active = flask_request.form.get('is_active') == '1'
        
        # Procesar valores opcionales
        vacation_days_override = None
        if vacation_days_str:
            vacation_days_override = int(vacation_days_str)
        
        hire_date = None
        if hire_date_str:
            hire_date = datetime.strptime(hire_date_str, '%Y-%m-%d').date()
        
        success, messages = user.update_profile(
            name=name if name else None,
            email=email if email else None,
            department_id=department_id,
            vacation_days_override=vacation_days_override,
            hire_date=hire_date,
            is_active=is_active
        )
        
        for message in messages:
            flash(message, 'success' if success else 'error')
            
    except ValueError:
        flash('Error en los valores introducidos.', 'error')
    except Exception as e:
        flash(f'Error al actualizar empleado: {str(e)}', 'error')
    
    return redirect(url_for('admin.employees'))

@admin_bp.route('/employees/<int:user_id>/deactivate', methods=['POST'])
@admin_required
def deactivate_employee(user_id):
    """Desactivar empleado"""
    user = User.query.get_or_404(user_id)
    
    success, message = user.deactivate_user()
    
    if success:
        flash(message, 'success')
    else:
        flash(message, 'error')
    
    return redirect(url_for('admin.employees'))

@admin_bp.route('/employees/<int:user_id>/reset-password', methods=['POST'])
@admin_required
def reset_password(user_id):
    """Resetear contraseña de empleado"""
    user = User.query.get_or_404(user_id)
    new_password = flask_request.form.get('new_password', 'temp123')
    
    try:
        user.set_password(new_password)
        db.session.commit()
        flash(f'Contraseña de {user.name} reseteada a: {new_password}', 'success')
    except Exception as e:
        flash(f'Error al resetear contraseña: {str(e)}', 'error')
        db.session.rollback()
    
    return redirect(url_for('admin.employees'))

# ============================================================================
# API ENDPOINTS PARA VALIDACIONES
# ============================================================================

@admin_bp.route('/api/validate-vacation-request')
@admin_required
def validate_vacation_request():
    """Validar solicitud de vacaciones para warnings de días excedentes"""
    try:
        user_id = int(flask_request.args.get('user_id'))
        start_date = datetime.strptime(flask_request.args.get('start_date'), '%Y-%m-%d').date()
        end_date = datetime.strptime(flask_request.args.get('end_date'), '%Y-%m-%d').date()
        
        user = User.query.get_or_404(user_id)
        
        # Verificar si excedería los días
        would_exceed, excess_days, details = user.would_exceed_vacation_days(start_date, end_date)
        
        # Obtener balance actual
        balance_info = user.get_vacation_balance_info(start_date.year)
        
        response_data = {
            'would_exceed': would_exceed,
            'excess_days': excess_days,
            'details': details,
            'balance_info': balance_info,
            'user_name': user.name
        }
        
        return jsonify(response_data)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@admin_bp.route('/api/employee/<int:user_id>/vacation-balance')
@admin_required
def employee_vacation_balance(user_id):
    """Obtener balance de vacaciones de un empleado"""
    try:
        user = User.query.get_or_404(user_id)
        year = int(flask_request.args.get('year', get_canary_time().year))
        
        balance_info = user.get_vacation_balance_info(year)
        
        return jsonify({
            'success': True,
            'balance': balance_info,
            'user_name': user.name
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 400

# Reactivar usuario

@admin_bp.route('/employees/<int:user_id>/reactivate', methods=['POST'])
@admin_required
def reactivate_employee(user_id):
    """Reactivar empleado"""
    user = User.query.get_or_404(user_id)
    
    try:
        user.is_active = True
        db.session.commit()
        flash(f'{user.name} ha sido reactivado correctamente.', 'success')
    except Exception as e:
        flash(f'Error al reactivar el empleado: {str(e)}', 'error')
        db.session.rollback()
    
    return redirect(url_for('admin.employees'))
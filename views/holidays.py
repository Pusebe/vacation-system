from flask import Blueprint, render_template, request as flask_request, redirect, url_for, flash, g
from utils import login_required, admin_required, create_notifications_for_new_holiday, create_notifications_for_new_request, get_canary_time
from models import db, WorkedHoliday, Request, Department, User
from datetime import datetime

holidays_bp = Blueprint('holidays', __name__)

@holidays_bp.route('/holidays')
@login_required
def index():
    """Lista de festivos trabajados"""
    if g.user.is_admin():
        # Admin ve todos los festivos
        all_holidays = WorkedHoliday.query.order_by(WorkedHoliday.date.desc()).all()
        pending_holidays = [h for h in all_holidays if h.status == 'pending']
        departments = Department.query.all()
        
        return render_template('holidays.html',
                             is_admin=True,
                             all_holidays=all_holidays,
                             pending_holidays=pending_holidays,
                             departments=departments,
                             common_holidays=WorkedHoliday.get_common_holidays())
    else:
        # Empleado ve solo sus festivos
        my_holidays = g.user.get_worked_holidays()
        
        # TODOS los festivos aprobados (para mostrar en la tabla)
        approved_holidays = WorkedHoliday.query.filter_by(
            user_id=g.user.id,
            status='approved'
        ).order_by(WorkedHoliday.date.desc()).all()
        
        # Calcular festivos disponibles
        available_holidays = []
        for holiday in approved_holidays:
            recovery_status, _ = holiday.get_recovery_status()
            # Disponible si no tiene recovery activa O si la anterior fue rechazada
            if not recovery_status or recovery_status == 'rejected':
                available_holidays.append(holiday)
        
        return render_template('holidays.html',
                            is_admin=False,
                            my_holidays=my_holidays,
                            approved_holidays=approved_holidays,
                            available_for_recovery=available_holidays,
                            available_count=len(available_holidays),
                            common_holidays=WorkedHoliday.get_common_holidays())

@holidays_bp.route('/holidays', methods=['POST'])
@login_required
def create():
    """Marcar festivo como trabajado"""
    try:
        # Obtener datos del formulario
        holiday_date = datetime.strptime(flask_request.form.get('date'), '%Y-%m-%d').date()
        description = flask_request.form.get('description', '').strip()
        
        # Si es admin y especifica user_id, crear para otro usuario
        if g.user.is_admin() and flask_request.form.get('user_id'):
            user_id = int(flask_request.form.get('user_id'))
            target_user = User.query.get_or_404(user_id)
            auto_approve = flask_request.form.get('auto_approve') == '1'
        else:
            user_id = g.user.id
            target_user = g.user
            auto_approve = False
        
        # Crear el festivo trabajado
        worked_holiday = WorkedHoliday(
            user_id=user_id,
            date=holiday_date,
            description=description
        )
        
        # Si es auto_approve, aprobar directamente
        if auto_approve:
            worked_holiday.status = 'approved'
            worked_holiday.approved_at = get_canary_time()
            worked_holiday.approved_by = g.user.id
        
        # Validar usando el fat model (solo si no es auto_approve)
        if not auto_approve:
            errors = worked_holiday.validate()
            if errors:
                for error in errors:
                    flash(error, 'error')
                return redirect(url_for('holidays.index'))
        
        # Guardar en base de datos
        db.session.add(worked_holiday)
        db.session.commit()
        
        # Crear notificaciones solo si no es auto_approve
        if not auto_approve:
            create_notifications_for_new_holiday(worked_holiday)
            flash('Festivo trabajado marcado correctamente. Pendiente de aprobación.', 'success')
        else:
            flash(f'Festivo trabajado marcado y aprobado para {target_user.name}.', 'success')
        
    except ValueError:
        flash('Error en el formato de la fecha.', 'error')
    except Exception as e:
        flash(f'Error al marcar el festivo: {str(e)}', 'error')
        db.session.rollback()
    
    return redirect(url_for('holidays.index'))

@holidays_bp.route('/holidays/<int:holiday_id>/approve', methods=['POST'])
@admin_required
def approve(holiday_id):
    """Aprobar festivo trabajado"""
    holiday = WorkedHoliday.query.get_or_404(holiday_id)
    
    # Usar método del fat model
    success, message = holiday.approve(g.user)
    
    if success:
        flash(message, 'success')
    else:
        flash(message, 'error')
    
    return redirect(url_for('holidays.index'))

@holidays_bp.route('/holidays/<int:holiday_id>/reject', methods=['POST'])
@admin_required
def reject(holiday_id):
    """Rechazar festivo trabajado"""
    holiday = WorkedHoliday.query.get_or_404(holiday_id)
    reject_reason = flask_request.form.get('reason', '').strip()
    
    # Usar método del fat model
    success, message = holiday.reject(g.user, reject_reason)
    
    if success:
        flash(message, 'success')
    else:
        flash(message, 'error')
    
    return redirect(url_for('holidays.index'))

@holidays_bp.route('/holidays/<int:holiday_id>/cancel', methods=['POST'])
@login_required
def cancel(holiday_id):
    """Cancelar festivo trabajado"""
    holiday = WorkedHoliday.query.get_or_404(holiday_id)
    
    # Verificar que sea el dueño del festivo o admin
    if holiday.user_id != g.user.id and not g.user.is_admin():
        flash('No tienes permisos para cancelar este festivo.', 'error')
        return redirect(url_for('holidays.index'))
    
    # Verificar si se puede cancelar usando fat model
    if not holiday.can_be_cancelled():
        flash('Este festivo no se puede cancelar.', 'error')
        return redirect(url_for('holidays.index'))
    
    # Usar método del fat model
    success, message = holiday.cancel()
    
    if success:
        flash(message, 'success')
    else:
        flash(message, 'error')
    
    return redirect(url_for('holidays.index'))

@holidays_bp.route('/holidays/<int:holiday_id>/create-recovery', methods=['POST'])
@login_required
def create_recovery(holiday_id):
    """Crear solicitud de recuperación usando un festivo trabajado"""
    holiday = WorkedHoliday.query.get_or_404(holiday_id)
    
    # Verificar que sea el dueño del festivo
    if holiday.user_id != g.user.id:
        flash('No tienes permisos para usar este festivo.', 'error')
        return redirect(url_for('holidays.index'))
    
    try:
        # Obtener datos del formulario
        recovery_date = datetime.strptime(flask_request.form.get('recovery_date'), '%Y-%m-%d').date()
        additional_reason = flask_request.form.get('reason', '').strip()
        
        # Usar método del fat model para crear la recuperación
        recovery_request, message = holiday.create_recovery_request(recovery_date, additional_reason)
        
        if recovery_request:
            # Validar la solicitud de recuperación
            errors = recovery_request.validate()
            if errors:
                for error in errors:
                    flash(error, 'error')
                return redirect(url_for('holidays.index'))
            
            # Guardar la solicitud
            db.session.add(recovery_request)
            db.session.commit()
            
            # Crear notificaciones
            create_notifications_for_new_request(recovery_request)
            
            flash('Solicitud de recuperación creada correctamente.', 'success')
        else:
            flash(message, 'error')
            
    except ValueError:
        flash('Error en el formato de la fecha.', 'error')
    except Exception as e:
        flash(f'Error al crear la recuperación: {str(e)}', 'error')
        db.session.rollback()
    
    return redirect(url_for('holidays.index'))

@holidays_bp.route('/holidays/<int:holiday_id>/edit', methods=['POST'])
@admin_required
def edit(holiday_id):
    """Editar festivo trabajado (solo admin)"""
    holiday = WorkedHoliday.query.get_or_404(holiday_id)
    
    try:
        # Obtener datos del formulario
        new_date = datetime.strptime(flask_request.form.get('date'), '%Y-%m-%d').date()
        new_description = flask_request.form.get('description', '').strip()
        new_status = flask_request.form.get('status')
        
        # Actualizar campos
        holiday.date = new_date
        holiday.description = new_description
        
        # Si cambia el estado, actualizar campos relacionados
        old_status = holiday.status
        holiday.status = new_status
        
        if new_status != old_status:
            if new_status in ['approved', 'rejected']:
                holiday.approved_at = get_canary_time()
                holiday.approved_by = g.user.id
            elif new_status == 'pending':
                holiday.approved_at = None
                holiday.approved_by = None
        
        db.session.commit()
        flash('Festivo actualizado correctamente.', 'success')
        
    except ValueError:
        flash('Error en el formato de la fecha.', 'error')
        db.session.rollback()
    except Exception as e:
        flash(f'Error al actualizar el festivo: {str(e)}', 'error')
        db.session.rollback()
    
    return redirect(url_for('holidays.index'))

@holidays_bp.route('/holidays/<int:holiday_id>/delete', methods=['POST'])
@admin_required
def delete(holiday_id):
    """Eliminar festivo trabajado (solo admin)"""
    holiday = WorkedHoliday.query.get_or_404(holiday_id)
    user_name = holiday.user.name
    holiday_date = holiday.date
    
    try:
        # Verificar si tiene solicitudes de recuperación asociadas
        if holiday.recovery_requests:
            recovery_count = len(holiday.recovery_requests)
            flash(f'No se puede eliminar: tiene {recovery_count} solicitud(es) de recuperación asociada(s).', 'error')
            return redirect(url_for('holidays.index'))
        
        db.session.delete(holiday)
        db.session.commit()
        flash(f'Festivo trabajado de {user_name} del {holiday_date.strftime("%d/%m/%Y")} eliminado correctamente.', 'success')
        
    except Exception as e:
        flash(f'Error al eliminar el festivo: {str(e)}', 'error')
        db.session.rollback()
    
    return redirect(url_for('holidays.index'))
from flask import Blueprint, render_template, request as flask_request, redirect, url_for, flash, g, jsonify
from utils import login_required, admin_required, create_notifications_for_new_request
from models import db, Request, User, Department, WorkedHoliday
from datetime import datetime

requests_bp = Blueprint('requests', __name__)

@requests_bp.route('/requests')
@login_required
def index():
    """Lista de solicitudes"""
    if g.user.is_admin():
        all_requests = Request.query.order_by(Request.created_at.desc()).all()
        pending_requests = Request.query.filter_by(status='pending').order_by(Request.created_at.desc()).all()
        departments = Department.query.all()
        
        return render_template('requests.html', 
                             is_admin=True,
                             all_requests=all_requests,
                             pending_requests=pending_requests,
                             departments=departments)
    else:
        my_requests = g.user.get_vacation_requests()
        my_recovery_requests = g.user.get_recovery_requests()
        
        return render_template('requests.html',
                             is_admin=False,
                             my_requests=my_requests,
                             my_recovery_requests=my_recovery_requests)

@requests_bp.route('/requests', methods=['POST'])
@login_required
def create():
    """Crear nueva solicitud"""
    try:
        request_type = flask_request.form.get('type')
        start_date = datetime.strptime(flask_request.form.get('start_date'), '%Y-%m-%d').date()
        end_date = datetime.strptime(flask_request.form.get('end_date'), '%Y-%m-%d').date()
        reason = flask_request.form.get('reason', '').strip()
        
        # Si es admin creando para otro usuario
        if g.user.is_admin() and flask_request.form.get('user_id'):
            user_id = int(flask_request.form.get('user_id'))
            target_user = User.query.get_or_404(user_id)
            auto_approve = flask_request.form.get('auto_approve') == '1'
        else:
            user_id = g.user.id
            target_user = g.user
            auto_approve = False
        
        # ✅ PARA RECOVERY: El admin debe especificar QUÉ festivo usar
        worked_holiday_id = None
        if request_type == 'recovery':
            # El admin debe pasar el ID del festivo a usar
            holiday_id = flask_request.form.get('worked_holiday_id')
            if not holiday_id:
                flash('Debes seleccionar qué festivo usar para la recuperación.', 'error')
                return redirect(url_for('requests.index'))
            
            # Verificar que el festivo existe y está disponible
            holiday = WorkedHoliday.query.filter_by(
                id=int(holiday_id),
                user_id=user_id,
                status='approved'
            ).first()
            
            if not holiday:
                flash('El festivo seleccionado no existe o no está disponible.', 'error')
                return redirect(url_for('requests.index'))
            
            # Verificar que no esté ya usado
            existing_recovery = Request.query.filter(
                Request.worked_holiday_id == holiday.id,
                Request.status.in_(['pending', 'approved'])
            ).first()
            
            if existing_recovery:
                flash(f'El festivo del {holiday.date.strftime("%d/%m/%Y")} ya está siendo usado para otra recuperación.', 'error')
                return redirect(url_for('requests.index'))
            
            worked_holiday_id = holiday.id
            
            # Recovery debe ser 1 día
            if start_date != end_date:
                flash('Las recuperaciones solo pueden ser de 1 día.', 'error')
                return redirect(url_for('requests.index'))
            
            # Agregar info del festivo al reason (igual que hace el empleado)
            reason = f"Recuperación por festivo trabajado el {holiday.date.strftime('%d/%m/%Y')}: {holiday.description or 'Sin descripción'}"
            if flask_request.form.get('reason'):
                reason += f"\n\nMotivo adicional: {flask_request.form.get('reason')}"
        
        # ✅ PARA VACATION: Solo verificar conflicto con otras vacaciones
        elif request_type == 'vacation':
            vacation_conflict = Request.query.filter(
                Request.user_id == user_id,
                Request.type == 'vacation',
                Request.status.in_(['pending', 'approved']),
                Request.start_date <= end_date,
                Request.end_date >= start_date
            ).first()
            
            if vacation_conflict:
                overlap_dates = f"{vacation_conflict.start_date.strftime('%d/%m/%Y')}"
                if vacation_conflict.start_date != vacation_conflict.end_date:
                    overlap_dates += f" a {vacation_conflict.end_date.strftime('%d/%m/%Y')}"
                
                error_msg = f"Las vacaciones se solapan con otras vacaciones {vacation_conflict.get_status_text().lower()} del {overlap_dates}."
                flash(error_msg, 'error')
                return redirect(url_for('requests.index'))
        
        # Crear la solicitud
        new_request = Request(
            user_id=user_id,
            type=request_type,
            start_date=start_date,
            end_date=end_date,
            reason=reason,
            worked_holiday_id=worked_holiday_id  # ✅ Vinculado al festivo si es recovery
        )
        
        db.session.add(new_request)
        db.session.commit()
        
        if auto_approve:
            success, message = new_request.approve(g.user)
            if success:
                flash(f'Solicitud de {new_request.get_type_text().lower()} creada y aprobada para {target_user.name}.', 'success')
            else:
                if isinstance(message, list):
                    for error in message:
                        flash(error, 'error')
                else:
                    flash(f'Error al aprobar: {message}', 'error')
        else:
            create_notifications_for_new_request(new_request)
            flash(f'Solicitud de {new_request.get_type_text().lower()} creada correctamente.', 'success')
        
    except ValueError:
        flash('Error en el formato de las fechas.', 'error')
    except Exception as e:
        flash(f'Error al crear la solicitud: {str(e)}', 'error')
        db.session.rollback()
    
    return redirect(url_for('requests.index'))

@requests_bp.route('/requests/<int:request_id>/approve', methods=['POST'])
@admin_required
def approve(request_id):
    """Aprobar solicitud existente"""
    request_obj = Request.query.get_or_404(request_id)
    
    # VACACIONES: Verificar conflictos antes de aprobar
    if request_obj.type == 'vacation':
        vacation_conflict = Request.query.filter(
            Request.user_id == request_obj.user_id,
            Request.type == 'vacation',
            Request.status.in_(['pending', 'approved']),
            Request.start_date <= request_obj.end_date,
            Request.end_date >= request_obj.start_date,
            Request.id != request_obj.id
        ).first()
        
        if vacation_conflict:
            overlap_dates = f"{vacation_conflict.start_date.strftime('%d/%m/%Y')}"
            if vacation_conflict.start_date != vacation_conflict.end_date:
                overlap_dates += f" a {vacation_conflict.end_date.strftime('%d/%m/%Y')}"
            
            error_msg = f"No se puede aprobar: {request_obj.user.name} ya tiene vacaciones {vacation_conflict.get_status_text().lower()} del {overlap_dates}."
            flash(error_msg, 'error')
            return redirect(url_for('requests.index'))
    
    # RECOVERY: Verificar que el festivo vinculado siga disponible
    elif request_obj.type == 'recovery':
        if request_obj.worked_holiday_id:
            holiday = WorkedHoliday.query.get(request_obj.worked_holiday_id)
            if not holiday or holiday.status != 'approved':
                flash(f"No se puede aprobar: el festivo vinculado ya no está disponible.", 'error')
                return redirect(url_for('requests.index'))
        else:
            flash(f"No se puede aprobar: solicitud de recuperación sin festivo vinculado.", 'error')
            return redirect(url_for('requests.index'))
    
    # Aprobar
    success, message = request_obj.approve(g.user)
    
    if success:
        flash(f'Solicitud de {request_obj.get_type_text().lower()} aprobada para {request_obj.user.name}.', 'success')
    else:
        if isinstance(message, list):
            for error in message:
                flash(error, 'error')
        else:
            flash(message, 'error')
    
    return redirect(url_for('requests.index'))

@requests_bp.route('/requests/<int:request_id>/reject', methods=['POST'])
@admin_required
def reject(request_id):
    request_obj = Request.query.get_or_404(request_id)
    reject_reason = flask_request.form.get('reason', '').strip()
    
    success, message = request_obj.reject(g.user, reject_reason)
    
    if success:
        flash(message, 'success')
    else:
        flash(message, 'error')
    
    return redirect(url_for('requests.index'))

@requests_bp.route('/requests/<int:request_id>/cancel', methods=['POST'])
@login_required
def cancel(request_id):
    request_obj = Request.query.get_or_404(request_id)
    
    if request_obj.user_id != g.user.id and not g.user.is_admin():
        flash('No tienes permisos para cancelar esta solicitud.', 'error')
        return redirect(url_for('requests.index'))
    
    if not request_obj.can_be_cancelled():
        flash('Esta solicitud no se puede cancelar.', 'error')
        return redirect(url_for('requests.index'))
    
    success, message = request_obj.cancel()
    
    if success:
        flash(message, 'success')
    else:
        flash(message, 'error')
    
    return redirect(url_for('requests.index'))

@requests_bp.route('/requests/<int:request_id>/edit', methods=['POST'])
@admin_required
def edit(request_id):
    request_obj = Request.query.get_or_404(request_id)
    
    try:
        updates = {}
        
        if flask_request.form.get('type'):
            updates['type'] = flask_request.form.get('type')
        
        if flask_request.form.get('start_date'):
            updates['start_date'] = datetime.strptime(flask_request.form.get('start_date'), '%Y-%m-%d').date()
        
        if flask_request.form.get('end_date'):
            updates['end_date'] = datetime.strptime(flask_request.form.get('end_date'), '%Y-%m-%d').date()
        
        if 'reason' in flask_request.form:
            updates['reason'] = flask_request.form.get('reason', '').strip()
        
        if flask_request.form.get('status'):
            updates['status'] = flask_request.form.get('status')
        
        success, message = request_obj.update(g.user, **updates)
        
        if success:
            flash(message, 'success')
        else:
            flash(message, 'error')
            
    except ValueError:
        flash('Error en el formato de las fechas.', 'error')
    except Exception as e:
        flash(f'Error al editar la solicitud: {str(e)}', 'error')
    
    return redirect(url_for('requests.index'))

@requests_bp.route('/requests/<int:request_id>/delete', methods=['POST'])
@admin_required
def delete(request_id):
    request_obj = Request.query.get_or_404(request_id)
    user_name = request_obj.user.name
    
    success, message = request_obj.delete()
    
    if success:
        flash(f'Solicitud de {user_name} eliminada correctamente.', 'success')
    else:
        flash(message, 'error')
    
    return redirect(url_for('requests.index'))
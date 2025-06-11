from flask import Blueprint, render_template, request as flask_request, redirect, url_for, flash, g, jsonify
from utils import login_required, admin_required, create_notifications_for_new_request
from models import db, Request, User, Department
from datetime import datetime

requests_bp = Blueprint('requests', __name__)

@requests_bp.route('/requests')
@login_required
def index():
    """Lista de solicitudes"""
    if g.user.is_admin():
        # Admin ve todas las solicitudes
        all_requests = Request.query.order_by(Request.created_at.desc()).all()
        pending_requests = Request.query.filter_by(status='pending').order_by(Request.created_at.desc()).all()
        departments = Department.query.all()
        
        return render_template('requests.html', 
                             is_admin=True,
                             all_requests=all_requests,
                             pending_requests=pending_requests,
                             departments=departments)
    else:
        # Empleado ve solo sus solicitudes
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
        # Obtener datos del formulario
        request_type = flask_request.form.get('type')  # 'vacation' o 'recovery'
        start_date = datetime.strptime(flask_request.form.get('start_date'), '%Y-%m-%d').date()
        end_date = datetime.strptime(flask_request.form.get('end_date'), '%Y-%m-%d').date()
        reason = flask_request.form.get('reason', '').strip()
        
        # Si es admin y especifica user_id, crear para otro usuario
        if g.user.is_admin() and flask_request.form.get('user_id'):
            user_id = int(flask_request.form.get('user_id'))
            target_user = User.query.get_or_404(user_id)
            auto_approve = flask_request.form.get('auto_approve') == '1'
        else:
            user_id = g.user.id
            target_user = g.user
            auto_approve = False
        
        # Crear la solicitud
        new_request = Request(
            user_id=user_id,
            type=request_type,
            start_date=start_date,
            end_date=end_date,
            reason=reason
        )
        
        # Validar usando el fat model (solo si no es admin con auto_approve)
        if not auto_approve:
            errors = new_request.validate()
            if errors:
                for error in errors:
                    flash(error, 'error')
                return redirect(url_for('requests.index'))
        
        # Guardar en base de datos
        db.session.add(new_request)
        db.session.commit()
        
        # Si es admin y auto_approve, aprobar inmediatamente
        if auto_approve:
            success, message = new_request.approve(g.user)
            if success:
                flash(f'Solicitud creada y aprobada para {target_user.name}.', 'success')
            else:
                flash(f'Solicitud creada pero error al aprobar: {message}', 'warning')
        else:
            # Crear notificaciones para administradores
            create_notifications_for_new_request(new_request)
            flash(f'Solicitud de {new_request.get_type_text().lower()} creada correctamente.', 'success')
        
    except ValueError as e:
        flash('Error en el formato de las fechas.', 'error')
    except Exception as e:
        flash(f'Error al crear la solicitud: {str(e)}', 'error')
        db.session.rollback()
    
    return redirect(url_for('requests.index'))

@requests_bp.route('/requests/<int:request_id>/approve', methods=['POST'])
@admin_required
def approve(request_id):
    """Aprobar solicitud"""
    request_obj = Request.query.get_or_404(request_id)
    
    # Usar método del fat model
    success, message = request_obj.approve(g.user)
    
    if success:
        flash(message, 'success')
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
    """Rechazar solicitud"""
    request_obj = Request.query.get_or_404(request_id)
    reject_reason = flask_request.form.get('reason', '').strip()
    
    # Usar método del fat model
    success, message = request_obj.reject(g.user, reject_reason)
    
    if success:
        flash(message, 'success')
    else:
        flash(message, 'error')
    
    return redirect(url_for('requests.index'))

@requests_bp.route('/requests/<int:request_id>/cancel', methods=['POST'])
@login_required
def cancel(request_id):
    """Cancelar solicitud"""
    request_obj = Request.query.get_or_404(request_id)
    
    # Verificar que sea el dueño de la solicitud o admin
    if request_obj.user_id != g.user.id and not g.user.is_admin():
        flash('No tienes permisos para cancelar esta solicitud.', 'error')
        return redirect(url_for('requests.index'))
    
    # Verificar si se puede cancelar usando fat model
    if not request_obj.can_be_cancelled():
        flash('Esta solicitud no se puede cancelar.', 'error')
        return redirect(url_for('requests.index'))
    
    # Usar método del fat model
    success, message = request_obj.cancel()
    
    if success:
        flash(message, 'success')
    else:
        flash(message, 'error')
    
    return redirect(url_for('requests.index'))

@requests_bp.route('/requests/<int:request_id>/edit', methods=['POST'])
@admin_required
def edit(request_id):
    """Editar solicitud (solo admin)"""
    request_obj = Request.query.get_or_404(request_id)
    
    try:
        # Obtener datos del formulario
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
        
        # Usar método del fat model
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
    """Eliminar solicitud (solo admin)"""
    request_obj = Request.query.get_or_404(request_id)
    user_name = request_obj.user.name
    
    # Usar método del fat model
    success, message = request_obj.delete()
    
    if success:
        flash(f'Solicitud de {user_name} eliminada correctamente.', 'success')
    else:
        flash(message, 'error')
    
    return redirect(url_for('requests.index'))
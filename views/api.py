from flask import Blueprint, jsonify, g, request as flask_request
from utils import login_required
from models import Notification, Request, WorkedHoliday, Department
from datetime import datetime, date, timedelta

api_bp = Blueprint('api', __name__, url_prefix='/api')

@api_bp.route('/notifications')
@login_required
def notifications():
    """Obtener número de notificaciones no leídas"""
    count = g.user.get_notifications_count() if g.user else 0
    return jsonify({'count': count})

@api_bp.route('/notifications/list')
@login_required
def notifications_list():
    """Obtener lista de notificaciones recientes"""
    notifications = g.user.get_recent_notifications(20) if g.user else []
    
    notifications_data = []
    for notif in notifications:
        notifications_data.append({
            'id': notif.id,
            'type': notif.type,
            'title': notif.title,
            'message': notif.message,
            'is_read': notif.is_read,
            'created_at': notif.created_at.isoformat(),
            'icon': notif.get_type_icon(),
            'class': notif.get_type_class()
        })
    
    return jsonify({'notifications': notifications_data})

@api_bp.route('/notifications/<int:notification_id>/read', methods=['POST'])
@login_required
def mark_notification_read(notification_id):
    """Marcar notificación como leída"""
    notification = Notification.query.filter_by(id=notification_id, user_id=g.user.id).first()
    
    if not notification:
        return jsonify({'success': False, 'error': 'Notificación no encontrada'}), 404
    
    success = notification.mark_as_read()
    return jsonify({'success': success})

@api_bp.route('/notifications/mark-all-read', methods=['POST'])
@login_required
def mark_all_notifications_read():
    """Marcar todas las notificaciones como leídas"""
    success = g.user.mark_all_notifications_read()
    return jsonify({'success': success})

@api_bp.route('/validate-dates')
@login_required
def validate_dates():
    """Validar disponibilidad de fechas para vacaciones y recuperaciones"""
    try:
        start_date = datetime.strptime(flask_request.args.get('start_date'), '%Y-%m-%d').date()
        end_date = datetime.strptime(flask_request.args.get('end_date'), '%Y-%m-%d').date()
        request_type = flask_request.args.get('type', 'vacation')
        
        if request_type == 'vacation':
            # Usar método del fat model para validar
            can_request, message = g.user.can_request_vacation(start_date, end_date)
            
            if can_request:
                # Calcular días
                days = (end_date - start_date).days + 1
                return jsonify({
                    'available': True,
                    'message': f'Fechas disponibles ({days} días)',
                    'days': days
                })
            else:
                return jsonify({
                    'available': False,
                    'message': message
                })
        else:  # recovery
            # Para recuperaciones, validaciones específicas
            if start_date != end_date:
                return jsonify({
                    'available': False,
                    'message': 'Las recuperaciones solo pueden ser de 1 día'
                })
            
            if start_date <= date.today():
                return jsonify({
                    'available': False,
                    'message': 'La fecha de recuperación debe ser futura'
                })
            
            # Verificar solapamiento con otras solicitudes
            if g.user.has_overlapping_requests(start_date, end_date):
                return jsonify({
                    'available': False,
                    'message': 'Ya tienes una solicitud para esta fecha'
                })
            
            return jsonify({
                'available': True,
                'message': 'Fecha válida para recuperación (1 día)',
                'days': 1
            })
                
    except ValueError:
        return jsonify({
            'available': False,
            'message': 'Formato de fecha inválido'
        })
    except Exception as e:
        return jsonify({
            'available': False,
            'message': f'Error: {str(e)}'
        })

@api_bp.route('/validate-recovery-date')
@login_required
def validate_recovery_date():
    """Validar fecha específica para recuperación de festivo"""
    try:
        recovery_date = datetime.strptime(flask_request.args.get('recovery_date'), '%Y-%m-%d').date()
        holiday_id = int(flask_request.args.get('holiday_id', 0))
        
        # Verificar que la fecha sea futura
        if recovery_date <= date.today():
            return jsonify({
                'valid': False,
                'message': 'La fecha de recuperación debe ser futura'
            })
        
        # Verificar que no hay solapamiento
        if g.user.has_overlapping_requests(recovery_date, recovery_date):
            return jsonify({
                'valid': False,
                'message': 'Ya tienes una solicitud para esta fecha'
            })
        
        # Verificar que el festivo existe y está disponible
        if holiday_id:
            holiday = WorkedHoliday.query.filter_by(id=holiday_id, user_id=g.user.id).first()
            if holiday:
                is_available, message = holiday.is_available_for_recovery()
                if not is_available:
                    return jsonify({
                        'valid': False,
                        'message': message
                    })
        
        return jsonify({
            'valid': True,
            'message': 'Fecha válida para recuperación'
        })
        
    except ValueError:
        return jsonify({
            'valid': False,
            'message': 'Formato de fecha inválido'
        })
    except Exception as e:
        return jsonify({
            'valid': False,
            'message': f'Error: {str(e)}'
        })

@api_bp.route('/calendar-events')
@login_required
def calendar_events():
    """Eventos para el calendario"""
    try:
        print(f"Usuario: {g.user.name}, Admin: {g.user.is_admin()}")  # Debug
        
        # Obtener rango de fechas (por defecto, 3 meses)
        start_str = flask_request.args.get('start')
        end_str = flask_request.args.get('end')
        
        print(f"Parámetros recibidos - start: {start_str}, end: {end_str}")  # Debug
        
        if start_str and end_str:
            try:
                # FullCalendar envía fechas en formato ISO: 2025-06-01T00:00:00+00:00
                # Intentar varios formatos
                if 'T' in start_str:
                    start_date = datetime.fromisoformat(start_str.replace('Z', '+00:00')).date()
                    end_date = datetime.fromisoformat(end_str.replace('Z', '+00:00')).date()
                else:
                    start_date = datetime.strptime(start_str, '%Y-%m-%d').date()
                    end_date = datetime.strptime(end_str, '%Y-%m-%d').date()
            except Exception as e:
                print(f"Error parseando fechas: {e}")
                # Fallback a rango por defecto
                today = date.today()
                start_date = today - timedelta(days=30)
                end_date = today + timedelta(days=90)
        else:
            # Rango por defecto
            today = date.today()
            start_date = today - timedelta(days=30)
            end_date = today + timedelta(days=90)
        
        print(f"Rango de fechas: {start_date} a {end_date}")  # Debug
        
        events = []
        
        if g.user.is_admin():
            print("Ejecutando lógica de admin...")  # Debug
            
            # Admin ve todas las vacaciones aprobadas
            approved_requests = Request.query.filter(
                Request.status == 'approved',
                Request.start_date <= end_date,
                Request.end_date >= start_date
            ).all()
            
            print(f"Solicitudes aprobadas encontradas: {len(approved_requests)}")  # Debug
            
            for req in approved_requests:
                print(f"Procesando solicitud: {req.user.name} - {req.start_date} a {req.end_date}")  # Debug
                
                if req.type == 'vacation':
                    color = '#0054a6'  # Azul para vacaciones aprobadas
                    title = req.user.name
                else:
                    color = '#f59f00'  # Naranja para recuperaciones aprobadas  
                    title = f'{req.user.name} (R)'
                
                events.append({
                    'id': f'{req.type}-{req.id}',
                    'title': title,
                    'start': req.start_date.isoformat(),
                    'end': (req.end_date + timedelta(days=1)).isoformat(),
                    'backgroundColor': color,
                    'borderColor': color,
                    'textColor': '#ffffff',
                    'extendedProps': {
                        'type': req.get_type_text(),
                        'user': req.user.name,
                        'department': req.user.department.name,
                        'requestId': req.id,
                        'status': 'Aprobada',
                        'days': (req.end_date - req.start_date).days + 1
                    }
                })
            
            # Admin también ve las PENDIENTES con colores diferentes
            pending_requests = Request.query.filter(
                Request.status == 'pending',
                Request.start_date <= end_date,
                Request.end_date >= start_date
            ).all()
            
            print(f"Solicitudes pendientes encontradas: {len(pending_requests)}")  # Debug
            
            for req in pending_requests:
                if req.type == 'vacation':
                    color = '#6c757d'  # Gris para vacaciones pendientes
                    title = f'{req.user.name} (Pendiente)'
                else:
                    color = '#ffc107'  # Amarillo para recuperaciones pendientes
                    title = f'{req.user.name} (R-Pendiente)'
                
                events.append({
                    'id': f'pending-{req.type}-{req.id}',
                    'title': title,
                    'start': req.start_date.isoformat(),
                    'end': (req.end_date + timedelta(days=1)).isoformat(),
                    'backgroundColor': color,
                    'borderColor': color,
                    'textColor': '#ffffff',
                    'display': 'background',  # Mostrar como fondo para diferenciar
                    'extendedProps': {
                        'type': req.get_type_text(),
                        'user': req.user.name,
                        'department': req.user.department.name,
                        'requestId': req.id,
                        'status': 'Pendiente',
                        'days': (req.end_date - req.start_date).days + 1
                    }
                })
                
        else:
            print("Ejecutando lógica de empleado...")  # Debug
            
            # Empleado ve sus vacaciones y las de su departamento
            
            # Mis vacaciones y recuperaciones
            my_requests = Request.query.filter(
                Request.user_id == g.user.id,
                Request.status == 'approved',
                Request.start_date <= end_date,
                Request.end_date >= start_date
            ).all()
            
            print(f"Mis solicitudes encontradas: {len(my_requests)}")  # Debug
            
            for req in my_requests:
                color = '#2fb344' if req.type == 'vacation' else '#f59f00'
                type_text = 'Vacaciones' if req.type == 'vacation' else 'Recuperación'
                days = (req.end_date - req.start_date).days + 1
                title = f'Mis {type_text}' + (f' ({days} días)' if days > 1 else ' (1 día)')
                
                events.append({
                    'id': f'{req.type}-{req.id}',
                    'title': title,
                    'start': req.start_date.isoformat(),
                    'end': (req.end_date + timedelta(days=1)).isoformat(),
                    'backgroundColor': color,
                    'borderColor': color,
                    'textColor': '#ffffff',
                    'extendedProps': {
                        'type': type_text,
                        'user': g.user.name,
                        'department': g.user.department.name,
                        'requestId': req.id,
                        'days': days
                    }
                })
            
            # Vacaciones de compañeros del departamento
            dept_employees = g.user.department.get_employees()
            dept_employee_ids = [emp.id for emp in dept_employees if emp.id != g.user.id]
            
            if dept_employee_ids:
                dept_requests = Request.query.filter(
                    Request.user_id.in_(dept_employee_ids),
                    Request.type == 'vacation',
                    Request.status == 'approved',
                    Request.start_date <= end_date,
                    Request.end_date >= start_date
                ).all()
                
                print(f"Solicitudes de compañeros encontradas: {len(dept_requests)}")  # Debug
                
                for req in dept_requests:
                    days = (req.end_date - req.start_date).days + 1
                    title = req.user.name + (f' ({days} días)' if days > 1 else ' (1 día)')
                    
                    events.append({
                        'id': f'dept-vacation-{req.id}',
                        'title': title,
                        'start': req.start_date.isoformat(),
                        'end': (req.end_date + timedelta(days=1)).isoformat(),
                        'backgroundColor': '#0ea5e9',
                        'borderColor': '#0ea5e9',
                        'textColor': '#ffffff',
                        'extendedProps': {
                            'type': 'Vacaciones',
                            'user': req.user.name,
                            'department': req.user.department.name,
                            'requestId': req.id,
                            'days': days
                        }
                    })
        
        print(f"Total eventos generados: {len(events)}")  # Debug
        return jsonify(events)
        
    except Exception as e:
        print(f"Error in calendar_events: {e}")  # Para debug
        import traceback
        traceback.print_exc()
        return jsonify([])  # Devolver array vacío en caso de error

@api_bp.route('/stats/department/<int:dept_id>')
@login_required
def department_stats(dept_id):
    """Estadísticas de un departamento (solo admin)"""
    if not g.user.is_admin():
        return jsonify({'error': 'No autorizado'}), 403
    
    department = Department.query.get_or_404(dept_id)
    stats = department.get_vacation_stats()
    
    # Agregar información adicional
    today = date.today()
    employees_on_vacation = department.get_employees_on_vacation(today, today)
    
    stats.update({
        'department_name': department.name,
        'department_id': department.id,
        'employees_on_vacation_count': len(employees_on_vacation),
        'employees_on_vacation': [emp.name for emp in employees_on_vacation],
        'can_approve_more': department.can_approve_vacation(today, today)
    })
    
    return jsonify(stats)
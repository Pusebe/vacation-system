from . import db
from utils import get_canary_time

class Notification(db.Model):
    __tablename__ = 'notifications'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    type = db.Column(db.String(50), nullable=False)  # 'request_pending', 'request_approved', etc.
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text)
    is_read = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=get_canary_time, nullable=False)
    
    # Para referenciar el objeto relacionado
    related_type = db.Column(db.String(50))  # 'request', 'holiday'
    related_id = db.Column(db.Integer)
    
    # Relación con el usuario
    user = db.relationship('User', backref='notifications')
    
    def __repr__(self):
        return f'<Notification {self.type} for {self.user.name}>'
    
    def mark_as_read(self):
        """Marcar notificación como leída"""
        self.is_read = True
        try:
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            return False
    
    def get_type_icon(self):
        """Obtener icono según el tipo de notificación"""
        icons = {
            'request_pending': 'clock',
            'request_approved': 'check-circle',
            'request_rejected': 'x-circle',
            'holiday_pending': 'calendar',
            'holiday_approved': 'calendar-check',
            'vacation_reminder': 'bell',
            'system': 'info-circle'
        }
        return icons.get(self.type, 'bell')
    
    def get_type_class(self):
        """Obtener clase CSS según el tipo"""
        classes = {
            'request_pending': 'text-warning',
            'request_approved': 'text-success',
            'request_rejected': 'text-danger',
            'holiday_pending': 'text-info',
            'holiday_approved': 'text-success',
            'vacation_reminder': 'text-primary',
            'system': 'text-muted'
        }
        return classes.get(self.type, 'text-muted')
    
    @staticmethod
    def create_for_admin_request(request_obj):
        """Crear notificación para admin sobre nueva solicitud"""
        from .user import User
        
        # Obtener todos los administradores
        admins = User.query.filter_by(role='admin', is_active=True).all()
        
        notifications = []
        for admin in admins:
            notification = Notification(
                user_id=admin.id,
                type='request_pending',
                title=f'Nueva solicitud de {request_obj.get_type_text().lower()}',
                message=f'{request_obj.user.name} ha solicitado {request_obj.get_type_text().lower()} del {request_obj.start_date} al {request_obj.end_date}',
                related_type='request',
                related_id=request_obj.id
            )
            notifications.append(notification)
        
        return notifications
    
    @staticmethod
    def create_for_admin_holiday(holiday_obj):
        """Crear notificación para admin sobre festivo trabajado"""
        from .user import User
        
        admins = User.query.filter_by(role='admin', is_active=True).all()
        
        notifications = []
        for admin in admins:
            notification = Notification(
                user_id=admin.id,
                type='holiday_pending',
                title='Nuevo festivo trabajado',
                message=f'{holiday_obj.user.name} marcó como trabajado el festivo del {holiday_obj.date}',
                related_type='holiday',
                related_id=holiday_obj.id
            )
            notifications.append(notification)
        
        return notifications
    
    @staticmethod
    def create_for_user_request_response(request_obj):
        """Crear notificación para usuario sobre respuesta a su solicitud"""
        if request_obj.status == 'approved':
            notification_type = 'request_approved'
            title = f'Solicitud de {request_obj.get_type_text().lower()} aprobada'
            message = f'Tu solicitud del {request_obj.start_date} al {request_obj.end_date} ha sido aprobada'
        else:
            notification_type = 'request_rejected'
            title = f'Solicitud de {request_obj.get_type_text().lower()} rechazada'
            message = f'Tu solicitud del {request_obj.start_date} al {request_obj.end_date} ha sido rechazada'
        
        return Notification(
            user_id=request_obj.user_id,
            type=notification_type,
            title=title,
            message=message,
            related_type='request',
            related_id=request_obj.id
        )
    
    @staticmethod
    def create_for_user_holiday_response(holiday_obj):
        """Crear notificación para usuario sobre aprobación de festivo"""
        return Notification(
            user_id=holiday_obj.user_id,
            type='holiday_approved',
            title='Festivo trabajado aprobado',
            message=f'Tu festivo trabajado del {holiday_obj.date} ha sido aprobado',
            related_type='holiday',
            related_id=holiday_obj.id
        )
    
    @staticmethod
    def create_for_user_holiday_rejection(holiday_obj):
        """Crear notificación para usuario sobre rechazo de festivo"""
        return Notification(
            user_id=holiday_obj.user_id,
            type='holiday_rejected',
            title='Festivo trabajado rechazado',
            message=f'Tu festivo trabajado del {holiday_obj.date} ha sido rechazado',
            related_type='holiday',
            related_id=holiday_obj.id
        )
    
    @staticmethod
    def mark_all_as_read_for_user(user_id):
        """Marcar todas las notificaciones de un usuario como leídas"""
        try:
            Notification.query.filter_by(user_id=user_id, is_read=False).update({'is_read': True})
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            return False
    
    @staticmethod
    def get_unread_count_for_user(user_id):
        """Obtener número de notificaciones no leídas para un usuario"""
        return Notification.query.filter_by(user_id=user_id, is_read=False).count()
    
    @staticmethod
    def get_recent_for_user(user_id, limit=10):
        """Obtener notificaciones recientes para un usuario"""
        return Notification.query.filter_by(user_id=user_id)\
                                .order_by(Notification.created_at.desc())\
                                .limit(limit).all()
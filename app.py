from flask import Flask, session, g
from config import Config
from models import db, User
import pytz
from datetime import datetime

def create_app():
    """Factory para crear la aplicación Flask"""
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Inicializar extensiones
    db.init_app(app)
    
    # Registrar blueprints
    from views.auth import auth_bp
    from views.dashboard import dashboard_bp
    from views.requests import requests_bp
    from views.holidays import holidays_bp
    from views.api import api_bp
    from views.calendar import calendar_bp
    from views.admin import admin_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(requests_bp)
    app.register_blueprint(holidays_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(calendar_bp)
    app.register_blueprint(admin_bp)
    
    # Configurar zona horaria y contexto global
    @app.before_request
    def load_logged_in_user():
        """Cargar usuario autenticado en g"""
        user_id = session.get('user_id')
        
        if user_id is None:
            g.user = None
        else:
            g.user = db.session.get(User, user_id)
            
            # Verificar que el usuario siga activo
            if g.user and not g.user.is_active:
                session.clear()
                g.user = None
    
    # Funciones de template disponibles globalmente
    @app.template_filter('datetime')
    def datetime_filter(datetime_obj, format='%d/%m/%Y %H:%M'):
        """Filtro para formatear fechas"""
        if not datetime_obj:
            return ''
        
        # Convertir a zona horaria de Canarias
        if datetime_obj.tzinfo is None:
            utc_time = pytz.utc.localize(datetime_obj)
        else:
            utc_time = datetime_obj
            
        canary_tz = pytz.timezone('Atlantic/Canary')
        canary_time = utc_time.astimezone(canary_tz)
        
        return canary_time.strftime(format)
    
    @app.template_filter('date')
    def date_filter(date_obj, format='%d/%m/%Y'):
        """Filtro para formatear fechas sin hora"""
        if not date_obj:
            return ''
        return date_obj.strftime(format)
    
    @app.template_global()
    def get_current_user():
        """Obtener usuario actual en templates"""
        return g.user
    
    @app.template_global()
    def get_notifications_count():
        """Obtener número de notificaciones no leídas"""
        if g.user:
            return g.user.get_notifications_count()
        return 0
    
    # Crear tablas si no existen
    with app.app_context():
        db.create_all()
        
        # Crear datos iniciales si es la primera vez
        create_initial_data()
        
        # Migrar datos existentes para nuevas columnas
        migrate_existing_data()
    
    return app

def create_initial_data():
    """Crear datos iniciales: departamentos y usuario admin"""
    from models import Department, User
    from werkzeug.security import generate_password_hash
    
    # Verificar si ya hay datos
    if User.query.first():
        return
    
    try:
        # Crear departamentos por defecto
        departments = [
            Department(name='Administración', max_concurrent_vacations=1, vacation_days_per_year=25),
            Department(name='Desarrollo', max_concurrent_vacations=1, vacation_days_per_year=22),
            Department(name='Marketing', max_concurrent_vacations=1, vacation_days_per_year=22),
            Department(name='Ventas', max_concurrent_vacations=1, vacation_days_per_year=22),
            Department(name='Recursos Humanos', max_concurrent_vacations=1, vacation_days_per_year=24)
        ]
        
        for dept in departments:
            db.session.add(dept)
        
        db.session.flush()  # Para obtener los IDs
        
        # Crear usuario administrador por defecto
        admin_user = User(
            email='admin@empresa.com',
            name='Administrador',
            department_id=departments[0].id,  # Administración
            role='admin',
            is_active=True,
            vacation_days_override=30  # Admin tiene más días
        )
        admin_user.set_password('admin123')  # Cambiar en primera configuración
        
        db.session.add(admin_user)
        
        # Crear algunos usuarios de ejemplo
        example_users = [
            {
                'email': 'juan.perez@empresa.com',
                'name': 'Juan Pérez',
                'department_id': departments[1].id,  # Desarrollo
                'password': 'user123',
                'vacation_days_override': None  # Usa los del departamento
            },
            {
                'email': 'maria.garcia@empresa.com',
                'name': 'María García',
                'department_id': departments[2].id,  # Marketing
                'password': 'user123',
                'vacation_days_override': 25  # Días personalizados
            },
            {
                'email': 'carlos.lopez@empresa.com',
                'name': 'Carlos López',
                'department_id': departments[1].id,  # Desarrollo
                'password': 'user123',
                'vacation_days_override': None
            }
        ]
        
        for user_data in example_users:
            user = User(
                email=user_data['email'],
                name=user_data['name'],
                department_id=user_data['department_id'],
                role='employee',
                is_active=True,
                vacation_days_override=user_data['vacation_days_override']
            )
            user.set_password(user_data['password'])
            db.session.add(user)
        
        db.session.commit()
        print("Datos iniciales creados correctamente")
        print("Usuario admin: admin@empresa.com / admin123")
        print("Usuarios ejemplo: juan.perez@empresa.com / user123")
        
    except Exception as e:
        db.session.rollback()
        print(f"Error creando datos iniciales: {e}")

def migrate_existing_data():
    """Migrar datos existentes para añadir nuevas columnas"""
    try:
        # Verificar si necesitamos añadir las nuevas columnas a la BD
        from sqlalchemy import inspect
        inspector = inspect(db.engine)
        
        # Verificar columnas en Department
        dept_columns = [col['name'] for col in inspector.get_columns('departments')]
        if 'vacation_days_per_year' not in dept_columns:
            print("Añadiendo columna vacation_days_per_year a departments...")
            db.engine.execute('ALTER TABLE departments ADD COLUMN vacation_days_per_year INTEGER DEFAULT 22')
            db.engine.execute('ALTER TABLE departments ADD COLUMN created_at DATETIME DEFAULT CURRENT_TIMESTAMP')
            db.engine.execute('ALTER TABLE departments ADD COLUMN updated_at DATETIME DEFAULT CURRENT_TIMESTAMP')
        
        # Verificar columnas en User
        user_columns = [col['name'] for col in inspector.get_columns('users')]
        if 'vacation_days_override' not in user_columns:
            print("Añadiendo columnas de gestión a users...")
            db.engine.execute('ALTER TABLE users ADD COLUMN vacation_days_override INTEGER')
            db.engine.execute('ALTER TABLE users ADD COLUMN hire_date DATE')
            db.engine.execute('ALTER TABLE users ADD COLUMN updated_at DATETIME DEFAULT CURRENT_TIMESTAMP')
        
        # Actualizar departamentos existentes con días por defecto
        from models import Department
        departments_without_days = Department.query.filter_by(vacation_days_per_year=None).all()
        for dept in departments_without_days:
            dept.vacation_days_per_year = 22  # Valor por defecto
        
        if departments_without_days:
            db.session.commit()
            print(f"Actualizados {len(departments_without_days)} departamentos con días por defecto")
        
    except Exception as e:
        print(f"Error en migración: {e}")
        # Continuar sin fallar, las migraciones son opcionales

if __name__ == '__main__':
    app = create_app()
    
    # Configuración para desarrollo/producción
    app.run(
        host='0.0.0.0',  # Accesible desde fuera
        port=5002,
        debug=False,  # En producción siempre False
        threaded=True
    )
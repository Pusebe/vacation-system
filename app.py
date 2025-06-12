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
        print("🔧 Iniciando creación de base de datos...")
        
        try:
            print("📋 Creando tablas...")
            db.create_all()
            print("✅ Tablas creadas exitosamente")
            
            print("🔄 Ejecutando migración...")
            migrate_existing_data()
            print("✅ Migración completada")
            
            print("👥 Creando datos iniciales...")
            create_initial_data()
            print("✅ Datos iniciales completados")
            
        except Exception as e:
            print(f"❌ Error durante la inicialización: {e}")
            import traceback
            traceback.print_exc()
    
    return app
    

def create_initial_data():
    """Crear datos iniciales: departamentos y usuario admin"""
    from models import Department, User
    from sqlalchemy import text
    from datetime import date  # ← ESTA LÍNEA FALTABA
    
    try:
        # Verificar si ya hay datos usando COUNT simple
        result = db.session.execute(text('SELECT COUNT(*) FROM users')).scalar()
        if result > 0:
            print("Ya existen datos en la base de datos")
            return
    except Exception as e:
        print(f"Base de datos vacía o nueva, creando datos iniciales...")
    
    try:
        # Crear departamentos por defecto
        cap_dept = Department(
            name='Capitanía', 
            max_concurrent_vacations=1,
            vacation_days_per_year=30
        )
        mar_dept = Department(
            name='Marinería', 
            max_concurrent_vacations=1,
            vacation_days_per_year=30
        )
        lim_dept = Department(
            name='Limpieza', 
            max_concurrent_vacations=1,
            vacation_days_per_year=30
        )
        
        db.session.add(cap_dept)
        db.session.add(mar_dept)
        db.session.add(lim_dept)
        db.session.flush()  # Para obtener los IDs
        
        # Crear usuario administrador
        admin_user = User(
            email='amorales@marinalanzarote.com',
            name='Alfredo',
            department_id=cap_dept.id,
            role='admin',
            is_active=True,
            vacation_days_override=30,
            hire_date=date.today()
        )
        admin_user.set_password('alfredo')
        db.session.add(admin_user)
        
        db.session.commit()
        print("Datos iniciales creados correctamente")
        
    except Exception as e:
        db.session.rollback()
        print(f"Error creando datos iniciales: {e}")
        # No hacer raise para que la app continúe

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
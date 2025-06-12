import os
from datetime import timedelta
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

class Config:
    # Configuración básica de Flask
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'fallback-key-change-immediately'
    
    # Base de datos
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///database.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Configuración de zona horaria
    TIMEZONE = os.environ.get('TIMEZONE') or 'Atlantic/Canary'
    
    # Configuración de sesiones - sesiones permanentes
    SESSION_PERMANENT = True
    PERMANENT_SESSION_LIFETIME = timedelta(seconds=int(os.environ.get('PERMANENT_SESSION_LIFETIME', 31536000)))  # 1 año por defecto
    SESSION_COOKIE_SECURE = True  # HTTPS en producción
    SESSION_COOKIE_HTTPONLY = True  # Prevenir acceso via JavaScript
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # Configuración de la aplicación
    APP_NAME = os.environ.get('APP_NAME') or 'Sistema de Vacaciones'
    ADMIN_EMAIL = os.environ.get('ADMIN_EMAIL') or 'admin@empresa.com'
    
    # Configuración de templates
    TEMPLATES_AUTO_RELOAD = False  # Desactivado en producción
    
    # Configuración de uploads (por si se necesita en el futuro)
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max
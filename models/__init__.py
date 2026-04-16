from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

# Importar todos los modelos para que estén disponibles
from .user import User
from .department import Department
from .request import Request
from .holiday import WorkedHoliday
from .notification import Notification
from .transaction import VacationTransaction

__all__ = ['db', 'User', 'Department', 'Request', 'WorkedHoliday', 'Notification', 'VacationTransaction']
from flask import Blueprint, render_template, g
from utils import login_required
from models import Department

calendar_bp = Blueprint('calendar', __name__)

@calendar_bp.route('/calendar')
@login_required
def index():
    """Página del calendario de vacaciones"""
    
    if g.user.is_admin():
        # Admin ve todo
        departments = Department.query.all()
        return render_template('calendar.html', 
                             is_admin=True,
                             departments=departments)
    else:
        # Empleado ve su departamento
        return render_template('calendar.html',
                             is_admin=False)
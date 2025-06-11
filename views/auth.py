from flask import Blueprint, render_template, request as flask_request, redirect, url_for, flash, session
from models import User
from werkzeug.security import check_password_hash

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Página de login"""
    if flask_request.method == 'POST':
        email = flask_request.form.get('email', '').strip()
        password = flask_request.form.get('password', '')
        if not email or not password:
            
            flash('Email y contraseña son obligatorios.', 'error')
            return render_template('login.html')
        
        # Buscar usuario
        user = User.query.filter_by(email=email).first()
        
        if user and user.check_password(password):
            if not user.is_active:
                flash('Tu cuenta está desactivada. Contacta con el administrador.', 'error')
                return render_template('login.html')
            
            # Iniciar sesión
            session.permanent = True  # Sesión permanente según config
            session['user_id'] = user.id
            session['user_name'] = user.name
            session['user_email'] = user.email
            session['user_role'] = user.role
            session['department_id'] = user.department_id
            session['department_name'] = user.department.name
            
            flash(f'¡Bienvenido, {user.name}!', 'success')
            
            # Redirigir según el parámetro 'next' o al dashboard

            next_page = flask_request.args.get('next')
            if next_page:
                return redirect(next_page)
            return redirect(url_for('dashboard.index'))
        else:
            flash('Email o contraseña incorrectos.', 'error')
    
    return render_template('login.html')

@auth_bp.route('/logout')
def logout():
    """Cerrar sesión"""
    user_name = session.get('user_name', 'Usuario')
    session.clear()
    flash(f'Hasta luego, {user_name}!', 'info')
    return redirect(url_for('auth.login'))
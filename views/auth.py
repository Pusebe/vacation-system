from flask import Blueprint, render_template, request as flask_request, redirect, url_for, flash, session, g
from models import User, db
from utils import login_required
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

# Añadir estos endpoints en views/auth.py

@auth_bp.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    """Cambiar contraseña del usuario"""
    if flask_request.method == 'POST':
        current_password = flask_request.form.get('current_password', '')
        new_password = flask_request.form.get('new_password', '')
        confirm_password = flask_request.form.get('confirm_password', '')
        
        # Validaciones
        if not current_password or not new_password or not confirm_password:
            flash('Todos los campos son obligatorios.', 'error')
            return render_template('change_password.html')
        
        # Verificar contraseña actual
        if not g.user.check_password(current_password):
            flash('La contraseña actual es incorrecta.', 'error')
            return render_template('change_password.html')
        
        # Verificar que las nuevas contraseñas coincidan
        if new_password != confirm_password:
            flash('Las nuevas contraseñas no coinciden.', 'error')
            return render_template('change_password.html')
        
        # Validar fortaleza de la nueva contraseña
        if len(new_password) < 6:
            flash('La nueva contraseña debe tener al menos 6 caracteres.', 'error')
            return render_template('change_password.html')
        
        # Verificar que no sea igual a la actual
        if g.user.check_password(new_password):
            flash('La nueva contraseña debe ser diferente a la actual.', 'error')
            return render_template('change_password.html')
        
        try:
            # Cambiar contraseña
            g.user.set_password(new_password)
            
            # Si tenía flag de cambio obligatorio, quitarlo
            if hasattr(g.user, 'must_change_password'):
                g.user.must_change_password = False
            
            db.session.commit()
            
            # Crear notificación de confirmación
            from models.notification import Notification
            notification = Notification(
                user_id=g.user.id,
                type='password_changed',
                title='Contraseña actualizada',
                message='Tu contraseña ha sido cambiada exitosamente.',
                related_type='user',
                related_id=g.user.id
            )
            db.session.add(notification)
            db.session.commit()
            
            flash('¡Contraseña cambiada exitosamente!', 'success')
            return redirect(url_for('dashboard.index'))
            
        except Exception as e:
            flash(f'Error al cambiar la contraseña: {str(e)}', 'error')
            db.session.rollback()
    
    return render_template('change_password.html')

@auth_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    """Perfil del usuario"""
    if flask_request.method == 'POST':
        name = flask_request.form.get('name', '').strip()
        
        if not name:
            flash('El nombre es obligatorio.', 'error')
            return render_template('profile.html')
        
        try:
            g.user.name = name
            db.session.commit()
            
            # Actualizar sesión
            session['user_name'] = name
            
            flash('Perfil actualizado correctamente.', 'success')
            
        except Exception as e:
            flash(f'Error al actualizar perfil: {str(e)}', 'error')
            db.session.rollback()
    
    return render_template('profile.html')
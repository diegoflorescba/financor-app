from flask import Blueprint, render_template, redirect, url_for, flash, request, session, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from datetime import datetime
from models import User, db
from auth import audit_change, admin_required
from sqlalchemy.exc import IntegrityError

auth = Blueprint('auth', __name__)

@auth.route('/login', methods=['GET', 'POST'])
def login():
    # Si el usuario ya está autenticado, redirigir a la página principal
    if current_user.is_authenticated:
        return redirect(url_for('index'))
        
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        remember = request.form.get('remember', '0') == '1'  # Por defecto no recordar
        
        if not username or not password:
            flash('Por favor ingrese usuario y contraseña', 'error')
            return render_template('auth/login.html')
            
        user = User.query.filter_by(username=username, password=password).first()
        
        if user:
            login_user(user, remember=remember)  # Usar el valor de remember
            user.last_login = datetime.utcnow()
            db.session.commit()
            flash('Inicio de sesión exitoso', 'success')
            # Redirigir a la página que el usuario intentaba acceder o a la página principal
            next_page = request.args.get('next')
            if next_page and next_page.startswith('/'):
                return redirect(next_page)
            return redirect(url_for('index'))
            
        flash('Usuario o contraseña incorrectos', 'error')
    return render_template('auth/login.html')

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    # Limpiar la sesión completamente
    session.clear()
    # Asegurarse de que el usuario sea redirigido al login
    flash('Sesión cerrada exitosamente', 'success')
    return redirect(url_for('auth.login'))

@auth.route('/profile')
@login_required
def profile():
    return render_template('auth/profile.html', user=current_user)

@auth.route('/change_password', methods=['GET', 'POST'])
@login_required
def change_password():
    if request.method == 'POST':
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        if current_user.password != current_password:
            flash('Contraseña actual incorrecta', 'error')
            return redirect(url_for('auth.change_password'))
            
        if new_password != confirm_password:
            flash('Las contraseñas no coinciden', 'error')
            return redirect(url_for('auth.change_password'))
            
        current_user.password = new_password
        db.session.commit()
        flash('Contraseña cambiada exitosamente', 'success')
        return redirect(url_for('auth.profile'))
        
    return render_template('auth/change_password.html')

@auth.route('/admin/users')
@login_required
@admin_required
def admin_users():
    users = User.query.all()
    return render_template('auth/admin_users.html', users=users, active_page='admin_users')

@auth.route('/create_user', methods=['POST'])
@login_required
@admin_required
def create_user():
    try:
        username = request.form.get('username')
        password = request.form.get('password')
        role = request.form.get('role', 'user')
        email = request.form.get('email')  # Email es opcional

        if not username or not password:
            flash('Usuario y contraseña son requeridos', 'error')
            return redirect(url_for('auth.admin_users'))

        # Verificar si el usuario ya existe
        if User.query.filter_by(username=username).first():
            flash('El nombre de usuario ya existe', 'error')
            return redirect(url_for('auth.admin_users'))

        # Verificar si el email ya existe (si se proporcionó uno)
        if email and User.query.filter_by(email=email).first():
            flash('El correo electrónico ya está en uso', 'error')
            return redirect(url_for('auth.admin_users'))

        new_user = User(
            username=username,
            email=email,  # Puede ser None
            role=role,
            is_active=True,
            created_by=current_user.id
        )
        new_user.set_password(password)

        db.session.add(new_user)
        db.session.commit()

        audit_change('create', 'user', new_user.id)
        flash('Usuario creado exitosamente', 'success')

    except IntegrityError:
        db.session.rollback()
        flash('Error: El nombre de usuario o correo electrónico ya existe', 'error')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al crear usuario: {str(e)}', 'error')

    return redirect(url_for('auth.admin_users'))

@auth.route('/user/<int:user_id>')
@login_required
@admin_required
def get_user(user_id):
    user = User.query.get_or_404(user_id)
    return jsonify({
        'id': user.id,
        'username': user.username,
        'is_admin': user.is_admin,
        'is_active': user.is_active
    })

@auth.route('/toggle_user_status/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def toggle_user_status(user_id):
    try:
        user = User.query.get_or_404(user_id)
        
        # No permitir desactivar usuarios administradores
        if user.is_admin:
            return jsonify({'success': False, 'message': 'No se puede desactivar un usuario administrador'})
        
        user.is_active = not user.is_active
        user.updated_by = current_user.id
        db.session.commit()
        
        audit_change('update', 'user', user.id)
        return jsonify({'success': True})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)})

@auth.route('/update_user', methods=['POST'])
@login_required
@admin_required
def update_user():
    try:
        user_id = request.form.get('user_id')
        username = request.form.get('username')
        password = request.form.get('password')
        is_admin = request.form.get('is_admin') == 'on'
        
        user = User.query.get_or_404(user_id)
        
        # Verificar si el nuevo username ya existe para otro usuario
        existing_user = User.query.filter(User.username == username, User.id != user.id).first()
        if existing_user:
            flash('El nombre de usuario ya existe', 'error')
            return redirect(url_for('auth.admin_users'))
        
        user.username = username
        user.role = 'admin' if is_admin else 'user'
        
        # Actualizar contraseña solo si se proporciona una nueva
        if password:
            user.password = password
            
        user.updated_by = current_user.id
        db.session.commit()
        
        audit_change('update', 'user', user.id)
        flash('Usuario actualizado exitosamente', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error al actualizar usuario: {str(e)}', 'error')
        
    return redirect(url_for('auth.admin_users')) 
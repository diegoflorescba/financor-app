from functools import wraps
from flask import abort, redirect, request, url_for
from flask_login import current_user
from models import AuditLog, db


def redirect_to_login():
    next_page = request.full_path if request.query_string else request.path
    return redirect(url_for('auth.login', next=next_page))

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect_to_login()
        if not current_user.is_admin:
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

def user_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect_to_login()
        return f(*args, **kwargs)
    return decorated_function

def audit_change(action, table_name, record_id, changes=None):
    """Registra un cambio en la base de datos"""
    if not current_user.is_authenticated:
        return
    try:
        audit = AuditLog(
            user_id=current_user.id,
            action=action,
            table_name=table_name,
            record_id=record_id,
            changes=changes
        )
        db.session.add(audit)
        db.session.flush()
    except Exception:
        pass

def get_changes(old_obj, new_obj):
    """Compara dos objetos y retorna los cambios"""
    changes = {}
    for column in old_obj.__table__.columns:
        old_value = getattr(old_obj, column.name)
        new_value = getattr(new_obj, column.name)
        if old_value != new_value:
            changes[column.name] = {
                'old': str(old_value),
                'new': str(new_value)
            }
    return changes 

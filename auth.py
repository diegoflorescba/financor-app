from functools import wraps
from flask import abort, current_app
from flask_login import current_user
from models import AuditLog, db

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

def user_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

def audit_change(action, table_name, record_id, changes=None):
    """Registra un cambio en la base de datos"""
    if current_user.is_authenticated:
        audit = AuditLog(
            user_id=current_user.id,
            action=action,
            table_name=table_name,
            record_id=record_id,
            changes=changes
        )
        db.session.add(audit)
        db.session.commit()

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
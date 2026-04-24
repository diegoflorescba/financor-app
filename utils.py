from flask import current_app
from flask_login import current_user
from .models import db, AuditLog

def audit_change(action, table_name, record_id, changes=None):
    """
    Log changes to the database
    
    Args:
        action (str): The type of action (create, update, delete)
        table_name (str): The name of the table being modified
        record_id (int): The ID of the record being modified
        changes (dict, optional): A dictionary containing the changes made
    """
    try:
        user_id = current_user.id if not current_user.is_anonymous else None
        
        audit_entry = AuditLog(
            action=action,
            table_name=table_name,
            record_id=record_id,
            changes=changes,
            user_id=user_id
        )
        
        db.session.add(audit_entry)
        db.session.commit()
        
        current_app.logger.info(
            f"Audit log created: {action} on {table_name} (ID: {record_id}) by user {user_id}"
        )
    except Exception as e:
        current_app.logger.error(f"Error creating audit log: {str(e)}")
        db.session.rollback() 
import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from sqlalchemy import inspect

def print_table_columns(table_name):
    inspector = inspect(db.engine)
    columns = inspector.get_columns(table_name)
    print(f"\nTabla: {table_name}")
    for col in columns:
        print(f"  - {col['name']} ({col['type']})")

if __name__ == '__main__':
    with app.app_context():
        print_table_columns('prestamo')
        print_table_columns('cuota') 
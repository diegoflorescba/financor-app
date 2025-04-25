from models import db, User
from app import app

def check_users():
    with app.app_context():
        users = User.query.all()
        print("\nUsuarios existentes:")
        print("-" * 50)
        print(f"{'Username':<20} {'Role':<15} {'Admin':<10} {'Active':<10}")
        print("-" * 50)
        for user in users:
            print(f"{user.username:<20} {user.role:<15} {str(user.is_admin):<10} {str(user.is_active):<10}")
        print("-" * 50)

if __name__ == '__main__':
    check_users() 
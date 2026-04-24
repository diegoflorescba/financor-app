from models import db, Prestamo
from app import app

if __name__ == "__main__":
    with app.app_context():
        prestamos = Prestamo.query.all()
        for prestamo in prestamos:
            print(f"Préstamo {prestamo.id_prestamo}: cuotas_pendientes = {prestamo.cuotas_pendientes}") 
import argparse
import os
import shutil
from datetime import datetime
from pathlib import Path

from dateutil.relativedelta import relativedelta
from flask import Flask

from models import (
    AuditLog,
    Cliente,
    Cuota,
    EstadoCuota,
    EstadoPrestamo,
    Garante,
    Pago,
    Prestamo,
    User,
    db,
)


BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "instance" / "prestamos.db"


def create_app():
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{DB_PATH}"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    db.init_app(app)
    return app


def backup_existing_db():
    if not DB_PATH.exists():
        return None

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = DB_PATH.with_name(f"prestamos_backup_before_seed_{timestamp}.db")
    shutil.copy2(DB_PATH, backup_path)
    return backup_path


def reset_database(skip_backup=False):
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    backup_path = None if skip_backup else backup_existing_db()

    if DB_PATH.exists():
        DB_PATH.unlink()

    return backup_path


def create_user(username, password, email, role):
    user = User(username=username, email=email, role=role, is_active=True)
    user.set_password(password)
    db.session.add(user)
    db.session.flush()
    return user


def add_audit(user, action, table_name, record_id, changes=None):
    db.session.add(
        AuditLog(
            user_id=user.id,
            action=action,
            table_name=table_name,
            record_id=record_id,
            changes=changes,
        )
    )


def create_cliente(admin, nombre, apellido, dni, telefono, email, direccion):
    cliente = Cliente(
        nombre=nombre,
        apellido=apellido,
        dni=dni,
        telefono=telefono,
        correo_electronico=email,
        direccion=direccion,
        documentacion_verificada=True,
        activo=True,
        created_by=admin.id,
    )
    db.session.add(cliente)
    db.session.flush()
    add_audit(admin, "create", "cliente", cliente.id_cliente)
    return cliente


def create_garante(nombre, apellido, dni, telefono, email, direccion):
    garante = Garante(
        nombre=nombre,
        apellido=apellido,
        dni=dni,
        telefono=telefono,
        correo_electronico=email,
        direccion=direccion,
        documentacion_verificada=True,
        activo=True,
    )
    db.session.add(garante)
    db.session.flush()
    return garante


def create_prestamo(
    admin,
    cliente,
    monto_prestado,
    tasa_interes,
    cuotas_totales,
    monto_cuota,
    primera_cuota,
    garante=None,
):
    prestamo = Prestamo(
        id_cliente=cliente.id_cliente,
        id_garante=garante.id_garante if garante else None,
        monto_prestado=monto_prestado,
        tasa_interes=tasa_interes,
        cuotas_totales=cuotas_totales,
        cuotas_pendientes=cuotas_totales,
        monto_cuotas=monto_cuota,
        monto_adeudado=monto_cuota * cuotas_totales,
        fecha_inicio=primera_cuota - relativedelta(months=1),
        estado=EstadoPrestamo.ACTIVO,
        created_by=admin.id,
    )
    db.session.add(prestamo)
    db.session.flush()

    for index in range(cuotas_totales):
        cuota = Cuota(
            id_prestamo=prestamo.id_prestamo,
            numero_cuota=index + 1,
            fecha_vencimiento=primera_cuota + relativedelta(months=index),
            monto=monto_cuota,
            monto_pagado=0.0,
            monto_pendiente=monto_cuota,
            estado=EstadoCuota.PENDIENTE,
            pagada=False,
            created_by=admin.id,
        )
        db.session.add(cuota)

    db.session.flush()
    add_audit(
        admin,
        "create",
        "prestamo",
        prestamo.id_prestamo,
        {
            "monto_prestado": monto_prestado,
            "cuotas_totales": cuotas_totales,
            "monto_cuotas": monto_cuota,
        },
    )
    return prestamo


def pay_cuota(cuota, amount, admin, tipo_pago="parcial", nota=None, interes=0.0):
    pago = cuota.registrar_pago_con_trazabilidad(
        monto_pagado=amount,
        interes_pagado=interes,
        tipo_pago=tipo_pago,
        nota=nota,
        usuario_id=admin.id,
    )
    pago.fecha_pago = datetime.now()
    return pago


def refresh_prestamo(prestamo):
    prestamo.actualizar_cuotas_pendientes()
    prestamo.monto_adeudado = sum(
        cuota.monto_pendiente or 0 for cuota in prestamo.cuotas if cuota.estado != EstadoCuota.PAGADA
    )
    prestamo.verificar_estado()


def seed_data():
    admin = create_user("admin", "admin123", "admin@example.com", "admin")
    create_user("operador", "user123", "operador@example.com", "user")
    add_audit(admin, "create", "user", admin.id, {"username": admin.username, "role": admin.role})

    garante = create_garante(
        "Marcela",
        "Suarez",
        "25999888",
        "3515550101",
        "marcela.suarez@example.com",
        "Av. Colon 1800, Cordoba",
    )
    add_audit(admin, "create", "garante", garante.id_garante)

    today = datetime.now().replace(hour=10, minute=0, second=0, microsecond=0)

    cliente_activo = create_cliente(
        admin,
        "Lucia",
        "Fernandez",
        "30111222",
        "3515551001",
        "lucia.fernandez@example.com",
        "Bv. San Juan 450, Cordoba",
    )
    prestamo_activo = create_prestamo(
        admin,
        cliente_activo,
        monto_prestado=300000,
        tasa_interes=45,
        cuotas_totales=6,
        monto_cuota=70000,
        primera_cuota=today - relativedelta(months=1),
        garante=garante,
    )
    pay_cuota(prestamo_activo.cuotas[0], 70000, admin, tipo_pago="total", nota="Pago completo inicial")
    pay_cuota(prestamo_activo.cuotas[1], 30000, admin, tipo_pago="parcial", nota="Pago parcial de prueba")
    refresh_prestamo(prestamo_activo)

    cliente_finalizado = create_cliente(
        admin,
        "Roberto",
        "Molina",
        "28777666",
        "3515551002",
        "roberto.molina@example.com",
        "Belgrano 920, Villa Allende",
    )
    prestamo_finalizado = create_prestamo(
        admin,
        cliente_finalizado,
        monto_prestado=120000,
        tasa_interes=35,
        cuotas_totales=3,
        monto_cuota=50000,
        primera_cuota=today - relativedelta(months=4),
    )
    for cuota in prestamo_finalizado.cuotas:
        pay_cuota(cuota, cuota.monto, admin, tipo_pago="total", nota="Saldo demo")
    refresh_prestamo(prestamo_finalizado)

    cliente_judicial = create_cliente(
        admin,
        "Carolina",
        "Paz",
        "33444555",
        "3515551003",
        "carolina.paz@example.com",
        "Rivadavia 135, Alta Gracia",
    )
    prestamo_judicial = create_prestamo(
        admin,
        cliente_judicial,
        monto_prestado=250000,
        tasa_interes=50,
        cuotas_totales=5,
        monto_cuota=65000,
        primera_cuota=today - relativedelta(months=3),
    )
    pay_cuota(prestamo_judicial.cuotas[0], 65000, admin, tipo_pago="total", nota="Pago antes de judicializar")
    prestamo_judicial.marcar_judicial()
    refresh_prestamo(prestamo_judicial)
    add_audit(
        admin,
        "update",
        "prestamo",
        prestamo_judicial.id_prestamo,
        {"estado": "JUDICIAL", "motivo": "Caso demo con cuotas vencidas"},
    )

    create_cliente(
        admin,
        "Matias",
        "Romero",
        "35666777",
        "3515551004",
        "matias.romero@example.com",
        "San Martin 720, Cordoba",
    )

    db.session.commit()


def print_summary(backup_path):
    print("Base de datos de prueba creada correctamente.")
    if backup_path:
        print(f"Backup anterior: {backup_path}")
    print(f"Base activa: {DB_PATH}")
    print("")
    print("Usuarios para ingresar:")
    print("  admin / admin123")
    print("  operador / user123")
    print("")
    print("Datos cargados:")
    print(f"  Clientes: {Cliente.query.count()}")
    print(f"  Garantes: {Garante.query.count()}")
    print(f"  Prestamos: {Prestamo.query.count()}")
    print(f"  Cuotas: {Cuota.query.count()}")
    print(f"  Pagos: {Pago.query.count()}")


def main():
    parser = argparse.ArgumentParser(description="Recrea la base local con datos de prueba.")
    parser.add_argument("--no-backup", action="store_true", help="No crear backup de la base existente.")
    args = parser.parse_args()

    backup_path = reset_database(skip_backup=args.no_backup)
    app = create_app()

    with app.app_context():
        db.create_all()
        seed_data()
        print_summary(backup_path)


if __name__ == "__main__":
    main()

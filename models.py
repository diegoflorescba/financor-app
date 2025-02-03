from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

# Crear la instancia de SQLAlchemy
db = SQLAlchemy()

# Definición de modelos


class Cliente(db.Model):
    __tablename__ = 'cliente'

    id_cliente = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    apellido = db.Column(db.String(100), nullable=False)
    dni = db.Column(db.String(20), unique=True, nullable=False)
    telefono = db.Column(db.String(20))
    direccion = db.Column(db.String(200))
    correo_electronico = db.Column(db.String(120))
    documentacion_verificada = db.Column(db.Boolean, default=False)
    fecha_registro = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    activo = db.Column(db.Boolean, default=True)
    prestamos = db.relationship('Prestamo', backref='cliente', lazy=True)

    def __repr__(self):
        return f'<Cliente {self.nombre} {self.apellido}>'


class Garante(db.Model):
    __tablename__ = 'garante'

    id_garante = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    apellido = db.Column(db.String(100), nullable=False)
    dni = db.Column(db.String(20), unique=True, nullable=False)
    telefono = db.Column(db.String(20))
    direccion = db.Column(db.String(200))
    correo_electronico = db.Column(db.String(120))
    documentacion_verificada = db.Column(db.Boolean, default=False)
    fecha_registro = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    activo = db.Column(db.Boolean, default=True)
    prestamos_garantizados = db.relationship('Prestamo', backref='garante', lazy=True)

    def __repr__(self):
        return f'<Garante {self.nombre} {self.apellido}>'


class Prestamo(db.Model):
    __tablename__ = 'prestamo'

    id_prestamo = db.Column(db.Integer, primary_key=True)
    fecha_inicio = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    fecha_finalizacion = db.Column(db.DateTime, nullable=False)
    monto_prestado = db.Column(db.Float, nullable=False)
    tasa_interes = db.Column(db.Float, nullable=False)
    cuotas_totales = db.Column(db.Integer, nullable=False)
    cuotas_pendientes = db.Column(db.Integer, nullable=False)
    monto_cuotas = db.Column(db.Float, nullable=False)
    monto_adeudado = db.Column(db.Float, nullable=False)
    estado = db.Column(db.String(20), default='ACTIVO')
    fecha_ultima_actualizacion = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    id_cliente = db.Column(db.Integer, db.ForeignKey('cliente.id_cliente'), nullable=False)
    id_garante = db.Column(db.Integer, db.ForeignKey('garante.id_garante'), nullable=True)
    cuotas = db.relationship('Cuota', backref='prestamo', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Prestamo {self.id_prestamo} - Cliente {self.id_cliente}>'


class Cuota(db.Model):
    __tablename__ = 'cuota'

    id_cuota = db.Column(db.Integer, primary_key=True)
    numero_cuota = db.Column(db.Integer, nullable=False)
    fecha_vencimiento = db.Column(db.DateTime, nullable=False)
    fecha_pago = db.Column(db.DateTime, nullable=True)
    monto = db.Column(db.Float, nullable=False)
    monto_pagado = db.Column(db.Float, default=0.0)
    pagada = db.Column(db.Boolean, default=False)
    estado = db.Column(db.String(20), default='PENDIENTE')  # PENDIENTE, PAGADA, VENCIDA
    id_prestamo = db.Column(db.Integer, db.ForeignKey('prestamo.id_prestamo'), nullable=False)

    def __repr__(self):
        return f'<Cuota {self.numero_cuota} del Préstamo {self.id_prestamo}>'

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask_login import UserMixin
from sqlalchemy.dialects.postgresql import JSON

# Crear la instancia de SQLAlchemy
db = SQLAlchemy()

# Definición de modelos

class User(UserMixin, db.Model):
    __tablename__ = 'user'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=True)
    password = db.Column(db.String(128))
    role = db.Column(db.String(20), nullable=False, default='user')
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    updated_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    
    # Relaciones
    creator = db.relationship('User', remote_side=[id], foreign_keys=[created_by], backref='created_users')
    updater = db.relationship('User', remote_side=[id], foreign_keys=[updated_by], backref='updated_users')
    
    # Relaciones
    clientes = db.relationship('Cliente', 
                             foreign_keys='Cliente.created_by',
                             backref=db.backref('created_by_user', lazy=True))
    
    prestamos = db.relationship('Prestamo',
                              foreign_keys='Prestamo.created_by',
                              backref=db.backref('created_by_user', lazy=True))
    
    @property
    def is_admin(self):
        return self.role == 'admin'
    
    def set_password(self, password):
        """Establece la contraseña del usuario."""
        self.password = password  # En este caso guardamos la contraseña en texto plano
        
    def check_password(self, password):
        """Verifica la contraseña del usuario."""
        return self.password == password  # Comparación directa ya que está en texto plano
    
    def __repr__(self):
        return f'<User {self.username}>'

class AuditLog(db.Model):
    __tablename__ = 'audit_log'
    
    id = db.Column(db.Integer, primary_key=True)
    action = db.Column(db.String(50), nullable=False)  # create, update, delete
    table_name = db.Column(db.String(50), nullable=False)
    record_id = db.Column(db.Integer, nullable=False)
    changes = db.Column(JSON, nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    user = db.relationship('User', backref=db.backref('audit_logs', lazy=True))

    def __repr__(self):
        return f'<AuditLog {self.action} {self.table_name} {self.record_id}>'

class Cliente(db.Model):
    __tablename__ = 'cliente'

    id_cliente = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nombre = db.Column(db.String(100), nullable=False)
    apellido = db.Column(db.String(100), nullable=False)
    dni = db.Column(db.String(20), unique=True, nullable=False)
    telefono = db.Column(db.String(20))
    correo_electronico = db.Column(db.String(120))
    direccion = db.Column(db.String(200))
    documentacion_verificada = db.Column(db.Boolean, default=False)
    fecha_registro = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    activo = db.Column(db.Boolean, default=True)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    updated_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)
    prestamos = db.relationship('Prestamo', back_populates='cliente')

    def __repr__(self):
        return f'<Cliente {self.nombre} {self.apellido}>'


class Garante(db.Model):
    __tablename__ = 'garante'

    id_garante = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nombre = db.Column(db.String(100), nullable=False)
    apellido = db.Column(db.String(100), nullable=False)
    dni = db.Column(db.String(20), unique=True, nullable=False)
    telefono = db.Column(db.String(20))
    correo_electronico = db.Column(db.String(120))
    direccion = db.Column(db.String(200))
    documentacion_verificada = db.Column(db.Boolean, default=False)
    activo = db.Column(db.Boolean, default=True)
    prestamos = db.relationship('Prestamo', back_populates='garante')

    def __repr__(self):
        return f'<Garante {self.nombre} {self.apellido}>'


class Prestamo(db.Model):
    __tablename__ = 'prestamo'

    id_prestamo = db.Column(db.Integer, primary_key=True, autoincrement=True)
    id_cliente = db.Column(db.Integer, db.ForeignKey('cliente.id_cliente'), nullable=False)
    id_garante = db.Column(db.Integer, db.ForeignKey('garante.id_garante'), nullable=True)
    monto_prestado = db.Column(db.Float, nullable=False)
    tasa_interes = db.Column(db.Float, nullable=False)
    cuotas_totales = db.Column(db.Integer, nullable=False)
    cuotas_pendientes = db.Column(db.Integer, nullable=False)
    monto_cuotas = db.Column(db.Float, nullable=False)
    monto_adeudado = db.Column(db.Float, nullable=False)
    fecha_inicio = db.Column(db.DateTime, nullable=False)
    fecha_finalizacion = db.Column(db.DateTime, nullable=True)
    estado = db.Column(db.String(20), nullable=False, default='ACTIVO')
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    updated_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)
    fecha_ultima_actualizacion = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relaciones
    cliente = db.relationship('Cliente', back_populates='prestamos')
    garante = db.relationship('Garante', back_populates='prestamos')
    cuotas = db.relationship('Cuota', back_populates='prestamo', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Prestamo {self.id_prestamo} - Cliente {self.id_cliente}>'


class Cuota(db.Model):
    __tablename__ = 'cuota'

    id_cuota = db.Column(db.Integer, primary_key=True, autoincrement=True)
    id_prestamo = db.Column(db.Integer, db.ForeignKey('prestamo.id_prestamo', ondelete='CASCADE'), nullable=False)
    numero_cuota = db.Column(db.Integer, nullable=False)
    fecha_vencimiento = db.Column(db.DateTime, nullable=False)
    fecha_pago = db.Column(db.DateTime, nullable=True)
    monto = db.Column(db.Float, nullable=False)
    monto_original = db.Column(db.Float, nullable=False)  # Monto original de la cuota
    monto_pendiente = db.Column(db.Float, nullable=False)  # Monto pendiente de pago
    monto_pagado = db.Column(db.Float, nullable=False, default=0.0)
    interes_acumulado = db.Column(db.Float, nullable=False, default=0.0)  # Interés acumulado
    fecha_ultimo_pago = db.Column(db.DateTime, nullable=True)  # Fecha del último pago
    ajuste_manual = db.Column(db.Float, nullable=True)  # Ajuste manual del monto
    nota_ajuste = db.Column(db.Text, nullable=True)  # Nota para el ajuste manual
    pagada = db.Column(db.Boolean, nullable=False, default=False)
    estado = db.Column(db.String(20), nullable=False, default='PENDIENTE')
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    updated_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)

    prestamo = db.relationship('Prestamo', back_populates='cuotas')

    def __repr__(self):
        return f'<Cuota {self.numero_cuota} del Préstamo {self.id_prestamo}>'

    def calcular_interes_diario(self):
        """Calcula el interés diario (0.5% por día) desde la fecha de vencimiento"""
        if self.pagada:
            return 0.0
        
        fecha_actual = datetime.now()
        if fecha_actual <= self.fecha_vencimiento:
            return 0.0
        
        dias_atraso = (fecha_actual - self.fecha_vencimiento).days
        interes = self.monto_pendiente * (0.005 * dias_atraso)
        return interes

    def monto_total_pendiente(self):
        """Retorna el monto total pendiente incluyendo intereses"""
        return self.monto_pendiente + self.interes_acumulado + self.calcular_interes_diario()

    def registrar_pago_parcial(self, monto_pagado, es_ajuste_manual=False, nota_ajuste=None):
        """Registra un pago parcial y actualiza los montos"""
        if monto_pagado <= 0:
            raise ValueError("El monto del pago debe ser mayor a 0")
        
        # Calcular interés hasta el momento del pago
        interes_hasta_ahora = self.calcular_interes_diario()
        self.interes_acumulado += interes_hasta_ahora
        
        # Actualizar montos
        self.monto_pagado += monto_pagado
        self.monto_pendiente -= monto_pagado
        self.fecha_ultimo_pago = datetime.now()
        
        # Si es un ajuste manual, registrar la nota
        if es_ajuste_manual:
            self.ajuste_manual = monto_pagado
            self.nota_ajuste = nota_ajuste
        
        # Verificar si la cuota está completamente pagada
        if self.monto_pendiente <= 0:
            self.pagada = True
            self.estado = 'PAGADA'
            self.fecha_pago = datetime.now()
        
        return True

    def actualizar_estado(self):
        """Actualiza el estado de la cuota basado en los montos"""
        if self.pagada:
            self.estado = 'PAGADA'
        elif self.monto_pendiente < self.monto_original:
            self.estado = 'PAGO_PARCIAL'
        else:
            self.estado = 'PENDIENTE'

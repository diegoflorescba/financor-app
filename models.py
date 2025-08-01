from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask_login import UserMixin
from sqlalchemy.dialects.postgresql import JSON
from enum import Enum

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

    def __repr__(self):
        return f'<Garante {self.nombre} {self.apellido}>'


class EstadoPrestamo(Enum):
    ACTIVO = "ACTIVO"
    JUDICIAL = "JUDICIAL"
    FINALIZADO = "FINALIZADO"

class EstadoCuota(Enum):
    PENDIENTE = "PENDIENTE"
    PAGO_PARCIAL = "PAGO_PARCIAL"
    JUDICIAL = "JUDICIAL"
    PAGADA = "PAGADA"

class Prestamo(db.Model):
    __tablename__ = 'prestamo'

    id_prestamo = db.Column(db.Integer, primary_key=True)
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
    estado = db.Column(db.Enum(EstadoPrestamo), nullable=False, default=EstadoPrestamo.ACTIVO)
    proceso_judicial = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    updated_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)

    # Relaciones
    cliente = db.relationship('Cliente', backref=db.backref('prestamos', lazy=True))
    garante = db.relationship('Garante', backref=db.backref('prestamos', lazy=True))
    cuotas = db.relationship('Cuota', backref='prestamo', lazy=True, cascade='all, delete-orphan')

    def marcar_judicial(self):
        """Marca el préstamo y sus cuotas pendientes como judiciales, actualizando el monto adeudado"""
        try:
            self.estado = EstadoPrestamo.JUDICIAL
            self.proceso_judicial = True
            monto_adeudado = 0
            for cuota in self.cuotas:
                if cuota.estado in [EstadoCuota.PENDIENTE, EstadoCuota.PAGO_PARCIAL]:
                    cuota.estado = EstadoCuota.JUDICIAL
                    cuota.proceso_judicial = True
                    monto_adeudado += (cuota.monto_pendiente or cuota.monto)
            self.monto_adeudado = monto_adeudado
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            raise e

    def verificar_estado(self):
        """Verifica y actualiza el estado del préstamo basado en sus cuotas"""
        if self.estado == EstadoPrestamo.JUDICIAL:
            return  # Si está en judicial, no cambia

        todas_pagadas = all(cuota.estado == EstadoCuota.PAGADA for cuota in self.cuotas)
        if todas_pagadas:
            self.estado = EstadoPrestamo.FINALIZADO
            self.fecha_finalizacion = datetime.now()
            db.session.commit()

    def actualizar_cuotas_pendientes(self):
        self.cuotas_pendientes = sum(1 for cuota in self.cuotas if cuota.estado in [EstadoCuota.PENDIENTE, EstadoCuota.PAGO_PARCIAL])
        db.session.commit()

    def __repr__(self):
        return f'<Prestamo {self.id_prestamo} - Cliente {self.id_cliente}>'

class Cuota(db.Model):
    __tablename__ = 'cuota'

    id_cuota = db.Column(db.Integer, primary_key=True)
    id_prestamo = db.Column(db.Integer, db.ForeignKey('prestamo.id_prestamo'), nullable=False)
    numero_cuota = db.Column(db.Integer, nullable=False)
    fecha_vencimiento = db.Column(db.DateTime, nullable=False)
    monto = db.Column(db.Float, nullable=False)
    monto_pagado = db.Column(db.Float, default=0.0)
    monto_pendiente = db.Column(db.Float, nullable=True)
    estado = db.Column(db.Enum(EstadoCuota), nullable=False, default=EstadoCuota.PENDIENTE)
    pagada = db.Column(db.Boolean, nullable=False, default=False)
    fecha_pago = db.Column(db.DateTime, nullable=True)
    nota_ajuste = db.Column(db.String(255), nullable=True)
    proceso_judicial = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    updated_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)

    def actualizar_estado(self, pagada=None, estado=None):
        """Actualiza el estado y el campo pagada manteniendo la sincronización"""
        if pagada is not None:
            self.pagada = pagada
            self.estado = EstadoCuota.PAGADA if pagada else EstadoCuota.PENDIENTE
        elif estado is not None:
            self.estado = estado
            self.pagada = (estado == EstadoCuota.PAGADA)

    def __repr__(self):
        return f'<Cuota {self.numero_cuota} del Préstamo {self.id_prestamo}>'

    def calcular_interes_diario(self):
        """Calcula el interés diario (0.5% por día) desde la fecha de vencimiento"""
        if self.estado == EstadoCuota.PAGADA:
            return 0.0
        
        fecha_actual = datetime.now()
        if fecha_actual <= self.fecha_vencimiento:
            return 0.0
        
        dias_atraso = (fecha_actual - self.fecha_vencimiento).days
        return self.monto_pendiente * 0.005 * dias_atraso  # 0.5% por día

    def monto_total_pendiente(self):
        """Retorna el monto total pendiente incluyendo intereses"""
        return self.monto_pendiente + self.calcular_interes_diario()

    def registrar_pago_parcial(self, monto_pagado, es_ajuste_manual=False, nota_ajuste=None):
        """Registra un pago parcial en la cuota"""
        if self.estado == EstadoCuota.JUDICIAL:
            raise ValueError("No se pueden registrar pagos en cuotas en estado judicial")
        
        self.monto_pagado += monto_pagado
        self.monto_pendiente = max(0, self.monto - self.monto_pagado)
        
        # Actualizar estado
        if self.monto_pendiente <= 0:
            self.estado = EstadoCuota.PAGADA
            self.fecha_pago = datetime.now()
        
        # Actualizar estado basado en montos
        self.actualizar_estado()
        
        if nota_ajuste:
            self.nota_ajuste = nota_ajuste
        
        # Actualizar cuotas pendientes del préstamo
        self.prestamo.actualizar_cuotas_pendientes()

    def registrar_pago(self, monto_pagado):
        """Registra un pago en la cuota y actualiza su estado"""
        if self.estado == EstadoCuota.JUDICIAL:
            raise ValueError("No se pueden registrar pagos en cuotas en estado judicial")

        self.monto_pagado = monto_pagado
        self.monto_pendiente = self.monto - monto_pagado
        
        if monto_pagado >= self.monto:
            self.estado = EstadoCuota.PAGADA
            self.monto_pagado = self.monto
            self.monto_pendiente = 0
            self.fecha_pago = datetime.now()
        elif monto_pagado > 0:
            self.estado = EstadoCuota.PAGO_PARCIAL
            self.fecha_pago = datetime.now()
        
        # Verificar estado del préstamo
        self.prestamo.verificar_estado()
        # Actualizar cuotas pendientes del préstamo
        self.prestamo.actualizar_cuotas_pendientes()
        db.session.commit()

    def registrar_pago_con_trazabilidad(self, monto_pagado, interes_pagado=None, tipo_pago='parcial', nota=None, usuario_id=None):
        """Registra un pago con trazabilidad completa en la tabla de pagos"""
        if self.estado == EstadoCuota.JUDICIAL:
            raise ValueError("No se pueden registrar pagos en cuotas en estado judicial")
        
        # Asegurar que interes_pagado tenga un valor válido
        interes_pagado = float(interes_pagado if interes_pagado is not None else 0.0)
        
        # Crear registro en la tabla de pagos
        pago = Pago(
            id_cuota=self.id_cuota,
            monto_pagado=monto_pagado,
            interes_pagado=interes_pagado,
            tipo_pago=tipo_pago,
            nota=nota,
            created_by=usuario_id
        )
        db.session.add(pago)
        
        # Actualizar la cuota
        self.monto_pagado += monto_pagado
        self.monto_pendiente = max(0, self.monto - self.monto_pagado)
        
        # Actualizar estado
        if self.monto_pendiente <= 0:
            self.estado = EstadoCuota.PAGADA
            self.fecha_pago = datetime.now()
        elif self.monto_pagado > 0:
            self.estado = EstadoCuota.PAGO_PARCIAL
            self.fecha_pago = datetime.now()
        
        # Actualizar cuotas pendientes del préstamo
        self.prestamo.actualizar_cuotas_pendientes()
        
        return pago

class Pago(db.Model):
    __tablename__ = 'pago'
    
    id_pago = db.Column(db.Integer, primary_key=True)
    id_cuota = db.Column(db.Integer, db.ForeignKey('cuota.id_cuota'), nullable=False)
    fecha_pago = db.Column(db.DateTime, nullable=False, default=datetime.now)
    monto_pagado = db.Column(db.Float, nullable=False)
    interes_pagado = db.Column(db.Float, nullable=True)
    tipo_pago = db.Column(db.String(20), nullable=False, default='parcial')  # 'parcial', 'total', 'ajuste'
    nota = db.Column(db.String(255), nullable=True)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    # Relaciones
    cuota = db.relationship('Cuota', backref=db.backref('pagos', lazy=True))
    created_by_user = db.relationship('User', backref=db.backref('pagos_registrados', lazy=True))
    
    def __repr__(self):
        return f'<Pago {self.id_pago} - Cuota {self.id_cuota} - ${self.monto_pagado}>'

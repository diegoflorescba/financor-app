from flask import Flask, render_template, request, redirect, url_for, flash, send_file, jsonify
from datetime import datetime, date, timedelta
from calendar import monthrange
from dateutil.relativedelta import relativedelta
from models import db, Cliente, Prestamo, Cuota, Garante
import os
import pandas as pd
import io
import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning
from sqlalchemy import or_, inspect, text, func
import locale
import json
import traceback
from docx import Document
from docx.shared import Pt


app = Flask(__name__)

# Suprimir advertencias de SSL inseguro
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

# Configuración más segura para producción
app.config.update(
    SECRET_KEY='tu_clave_secreta_aqui',
    SQLALCHEMY_DATABASE_URI='sqlite:///' + os.path.join(os.path.abspath(os.path.dirname(__file__)), 'instance', 'prestamos.db'),
    SQLALCHEMY_TRACK_MODIFICATIONS=False,
    SESSION_COOKIE_SECURE=True,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax',
)

# Inicializar la base de datos
db.init_app(app)

# Crear las tablas si no existen
with app.app_context():
    db.create_all()
    print("Base de datos inicializada correctamente")

# Configuración de la API BCRA
BCRA_API_URL = "https://api.bcra.gob.ar/centraldedeudores/v1.0/Deudas/{}"
BCRA_API_URL_HISTORICA = "https://api.bcra.gob.ar/centraldedeudores/v1.0/Deudas/Historicas/{}"


@app.route('/')
@app.route('/index')
def index():
    return render_template('index.html', active_page='inicio')


@app.route('/clientes')
def clientes():
    clientes_list = Cliente.query.order_by(Cliente.apellido).all()
    return render_template('clientes.html', clientes=clientes_list, active_page='clientes')


@app.route('/cliente/nuevo', methods=['GET', 'POST'])
def nuevo_cliente():
    if request.method == 'POST':
        try:
            nuevo_cliente = Cliente(
                nombre=request.form['nombre'],
                apellido=request.form['apellido'],
                dni=request.form['dni'],
                telefono=request.form['telefono'],
                correo_electronico=request.form.get('correo_electronico', ''),
                direccion=request.form.get('direccion', ''),
                documentacion_verificada=bool(request.form.get('documentacion_verificada')),
                fecha_registro=datetime.now(),
                activo=bool(request.form.get('activo', True))
            )
            db.session.add(nuevo_cliente)
            db.session.commit()
            flash('Cliente registrado exitosamente', 'success')
            return redirect(url_for('clientes'))

        except Exception as e:
            db.session.rollback()
            flash(f'Error al registrar el cliente: {str(e)}', 'error')

    return render_template('registro.html', datetime=datetime, active_page='clientes')


@app.route('/registro', methods=['GET', 'POST'])
def registro():
    if request.method == 'POST':
        try:
            # Verificar si ya existe un cliente con ese DNI
            dni = request.form['dni']
            cliente_existente = Cliente.query.filter_by(dni=dni).first()
            if cliente_existente:
                flash('Ya existe un cliente registrado con ese DNI', 'error')
                return redirect(url_for('registro'))

            # Crear cliente
            nuevo_cliente = Cliente(
                nombre=request.form['nombre'],
                apellido=request.form['apellido'],
                dni=dni,
                telefono=request.form['telefono'],
                correo_electronico=request.form['correo_electronico'],
                direccion=request.form['direccion']
            )
            db.session.add(nuevo_cliente)
            db.session.flush()  # Para obtener el id_cliente

            # Si se incluye préstamo
            if 'tiene_prestamo' in request.form:
                fecha_inicio = datetime.strptime(request.form['fecha_inicio'], '%Y-%m-%d')
                fecha_primera_cuota = datetime.strptime(request.form['fecha_vencimiento_primera_cuota'], '%Y-%m-%d')
                dia_vencimiento = fecha_primera_cuota.day

                # Usar los valores ingresados directamente
                monto_prestado = float(request.form['monto_prestado'])
                monto_cuota = float(request.form['monto_cuotas'])
                cuotas_totales = int(request.form['cuotas_totales'])
                tasa_interes = float(request.form['tasa_interes'])
                
                # Calcular monto total basado en cuotas y monto por cuota
                monto_total = monto_cuota * cuotas_totales

                # Crear el préstamo
                nuevo_prestamo = Prestamo(
                    id_cliente=nuevo_cliente.id_cliente,
                    monto_prestado=monto_prestado,
                    tasa_interes=tasa_interes,  # Solo informativo
                    cuotas_totales=cuotas_totales,
                    cuotas_pendientes=cuotas_totales,
                    monto_cuotas=monto_cuota,
                    monto_adeudado=monto_total,
                    fecha_inicio=fecha_inicio,
                    fecha_finalizacion=fecha_primera_cuota + relativedelta(months=cuotas_totales-1),
                    estado='ACTIVO'
                )

                db.session.add(nuevo_prestamo)
                db.session.flush()

                # Crear las cuotas
                hoy = datetime.now().date()
                cuotas_pagadas = 0
                monto_pagado = 0

                for i in range(cuotas_totales):
                    # Calcular fecha de vencimiento manteniendo el mismo día
                    if i == 0:
                        fecha_vencimiento = fecha_primera_cuota
                    else:
                        # Usar relativedelta para mantener el mismo día del mes
                        fecha_vencimiento = fecha_primera_cuota + relativedelta(months=i)
                        # Asegurar que se mantenga el día de vencimiento
                        fecha_vencimiento = fecha_vencimiento.replace(day=dia_vencimiento)
                    
                    # Verificar si la cuota ya venció
                    esta_pagada = fecha_vencimiento.date() < hoy
                    
                    nueva_cuota = Cuota(
                        id_prestamo=nuevo_prestamo.id_prestamo,
                        numero_cuota=i + 1,
                        fecha_vencimiento=fecha_vencimiento,
                        monto=monto_cuota,
                        monto_pagado=monto_cuota if esta_pagada else 0.0,
                        pagada=esta_pagada,
                        estado='PAGADA' if esta_pagada else 'PENDIENTE',
                        fecha_pago=datetime.now() if esta_pagada else None
                    )
                    
                    if esta_pagada:
                        cuotas_pagadas += 1
                        monto_pagado += monto_cuota
                    
                    db.session.add(nueva_cuota)

                # Actualizar el préstamo con las cuotas pagadas
                nuevo_prestamo.cuotas_pendientes = cuotas_totales - cuotas_pagadas
                nuevo_prestamo.monto_adeudado = monto_total - monto_pagado

                # Si todas las cuotas están pagadas, marcar el préstamo como finalizado
                if cuotas_pagadas == cuotas_totales:
                    nuevo_prestamo.estado = 'FINALIZADO'
                    nuevo_prestamo.fecha_finalizacion = datetime.now()

                # Procesar garante si está incluido
                if 'tiene_garante' in request.form:
                    dni_garante = request.form['dni_garante']
                    garante = Garante.query.filter_by(dni=dni_garante).first()

                    if not garante:
                        # Crear nuevo garante
                        garante = Garante(
                            nombre=request.form['nombre_garante'],
                            apellido=request.form['apellido_garante'],
                            dni=dni_garante,
                            telefono=request.form.get('telefono_garante', ''),
                            correo_electronico=request.form.get('correo_garante', ''),
                            direccion=request.form.get('direccion_garante', ''),
                            documentacion_verificada=True,
                            activo=True
                        )
                        db.session.add(garante)
                        db.session.flush()

                    nuevo_prestamo.id_garante = garante.id_garante

            db.session.commit()
            flash('Cliente registrado exitosamente', 'success')
            return redirect(url_for('clientes'))

        except Exception as e:
            db.session.rollback()
            flash(f'Error al registrar cliente: {str(e)}', 'error')
            return redirect(url_for('registro'))

    return render_template('registro.html')


@app.route('/reportes')
def reportes():
    # Configurar el locale en español
    locale.setlocale(locale.LC_TIME, 'es_ES.UTF-8')
    
    # Obtener fecha actual y siguiente
    fecha_actual = datetime.now()
    fecha_siguiente = fecha_actual + relativedelta(months=1)
    
    # Formatear nombres de meses
    mes_actual = fecha_actual.strftime('%B %Y').capitalize()
    mes_siguiente = fecha_siguiente.strftime('%B %Y').capitalize()
    
    # Obtener todos los préstamos activos
    prestamos = Prestamo.query.filter(
        Prestamo.estado == 'ACTIVO',
        Prestamo.monto_adeudado > 0
    ).all()
    
    # Modificar el cálculo del total adeudado para solo incluir cuotas pendientes
    total_adeudado = db.session.query(
        func.sum(Cuota.monto - Cuota.monto_pagado)
    ).join(
        Prestamo, Cuota.id_prestamo == Prestamo.id_prestamo
    ).filter(
        Cuota.estado == 'PENDIENTE',
        Prestamo.estado == 'ACTIVO'
    ).scalar() or 0
    
    # Calcular el adeudado del mes actual
    adeudado_mes_actual = db.session.query(db.func.sum(Cuota.monto))\
        .join(Prestamo)\
        .filter(
            Prestamo.estado == 'ACTIVO',
            Cuota.pagada == False,
            db.extract('month', Cuota.fecha_vencimiento) == fecha_actual.month,
            db.extract('year', Cuota.fecha_vencimiento) == fecha_actual.year
        ).scalar() or 0.0
    
    # Calcular el adeudado del mes siguiente
    adeudado_mes_siguiente = db.session.query(db.func.sum(Cuota.monto))\
        .join(Prestamo)\
        .filter(
            Prestamo.estado == 'ACTIVO',
            Cuota.pagada == False,
            db.extract('month', Cuota.fecha_vencimiento) == fecha_siguiente.month,
            db.extract('year', Cuota.fecha_vencimiento) == fecha_siguiente.year
        ).scalar() or 0.0

    # Obtener cuotas para la tabla
    query = Cuota.query.join(Prestamo).join(Cliente).filter(
        Prestamo.estado == 'ACTIVO',
        Cuota.pagada == False
    )

    # Si estamos después del día 10, incluir cuotas del mes siguiente
    if fecha_actual.day > 10:
        query = query.filter(
            db.or_(
                db.and_(
                    db.extract('month', Cuota.fecha_vencimiento) == fecha_actual.month,
                    db.extract('year', Cuota.fecha_vencimiento) == fecha_actual.year
                ),
                db.and_(
                    db.extract('month', Cuota.fecha_vencimiento) == fecha_siguiente.month,
                    db.extract('year', Cuota.fecha_vencimiento) == fecha_siguiente.year
                )
            )
        )
    else:
        query = query.filter(
            db.extract('month', Cuota.fecha_vencimiento) == fecha_actual.month,
            db.extract('year', Cuota.fecha_vencimiento) == fecha_actual.year
        )

    cuotas = query.order_by(Cliente.apellido, Cliente.nombre, Cuota.fecha_vencimiento).all()
    
    return render_template('reportes.html',
                         prestamos=prestamos,
                         cuotas=cuotas,
                         mes_actual=mes_actual,
                         mes_siguiente=mes_siguiente,
                         total_adeudado=total_adeudado,
                         adeudado_mes_actual=adeudado_mes_actual,
                         adeudado_mes_siguiente=adeudado_mes_siguiente,
                         active_page='reportes')


@app.route('/cuotas_a_vencer')
def cuotas_a_vencer():
    # Configurar el locale en español
    locale.setlocale(locale.LC_TIME, 'es_ES.UTF-8')
    
    today = date.today()
    # Capitalizar la primera letra del mes
    mes_actual = today.strftime('%B %Y').capitalize()
    
    # Filtrar cuotas:
    # - Del mes actual
    # - Que venzan antes del día 10
    # - Que no estén pagadas
    cuotas = Cuota.query.join(Prestamo).join(Cliente).filter(
        Cuota.fecha_vencimiento.between(
            datetime(today.year, today.month, 1),
            datetime(today.year, today.month, 10)
        ),
        Cuota.pagada == False
    ).order_by(Cuota.fecha_vencimiento).all()

    # Calcular el total a cobrar
    total_a_cobrar = sum(cuota.monto for cuota in cuotas)

    return render_template('cuotas_a_vencer.html',
                         cuotas=cuotas,
                         total_a_cobrar=total_a_cobrar,
                         today=today,
                         mes_actual=mes_actual)


@app.route('/cliente/<int:id>')
def ver_cliente(id):
    cliente = Cliente.query.get_or_404(id)
    return render_template('cliente_detalle.html', cliente=cliente)


@app.route('/cliente/editar/<int:id>', methods=['GET', 'POST'])
def editar_cliente(id):
    cliente = Cliente.query.get_or_404(id)
    
    if request.method == 'POST':
        try:
            cliente.nombre = request.form['nombre']
            cliente.apellido = request.form['apellido']
            cliente.dni = request.form['dni']
            cliente.telefono = request.form['telefono']
            cliente.correo_electronico = request.form['correo_electronico']
            cliente.direccion = request.form['direccion']
            
            db.session.commit()
            flash('Cliente actualizado exitosamente', 'success')
            return redirect(url_for('clientes'))
            
        except Exception as e:
            db.session.rollback()
            flash('Error al actualizar el cliente: ' + str(e), 'danger')
    
    return render_template('cliente_editar.html', 
                         cliente=cliente, 
                         active_page='clientes')


@app.route('/exportar_excel')
def exportar_excel():
    try:
        # Obtener el mes actual
        hoy = datetime.now()
        _, ultimo_dia = monthrange(hoy.year, hoy.month)

        # Crear fechas de inicio y fin del mes como datetime
        primer_dia_mes = datetime(hoy.year, hoy.month, 1)
        ultimo_dia_mes = datetime(hoy.year, hoy.month, ultimo_dia, 23, 59, 59)

        # Obtener cuotas del mes actual
        cuotas = Cuota.query.join(Prestamo).join(Cliente).filter(
            Cuota.fecha_vencimiento >= primer_dia_mes,
            Cuota.fecha_vencimiento <= ultimo_dia_mes,
            Cuota.pagada == False,
            Prestamo.estado == 'ACTIVO'
        ).order_by(Cliente.apellido, Cliente.nombre, Cuota.fecha_vencimiento).all()

        # Crear DataFrame
        data = []
        for cuota in cuotas:
            data.append({
                'Cliente': f"{cuota.prestamo.cliente.apellido}, {cuota.prestamo.cliente.nombre}",
                'Teléfono': cuota.prestamo.cliente.telefono,
                'Cuota': f"{cuota.numero_cuota}/{cuota.prestamo.cuotas_totales}",
                'Vencimiento': cuota.fecha_vencimiento.strftime('%d/%m/%Y'),
                'Monto': f"${cuota.monto:,.2f}",
                'Estado': 'PENDIENTE' if not cuota.pagada else 'PAGADA'
            })

        # Crear Excel
        df = pd.DataFrame(data)
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, sheet_name='Cuotas', index=False)

            # Ajustar columnas
            worksheet = writer.sheets['Cuotas']
            for idx, col in enumerate(df.columns):
                max_length = max(df[col].astype(
                    str).apply(len).max(), len(col))
                worksheet.set_column(idx, idx, max_length + 2)

        output.seek(0)

        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=f'cuotas_a_vencer_{hoy.strftime("%Y%m")}.xlsx'
        )

    except Exception as e:
        print(f"Error al exportar Excel: {str(e)}")
        flash('Error al exportar el archivo Excel', 'error')
        return redirect(url_for('cuotas_a_vencer'))


@app.template_filter('money')
def money_format(value):
    try:
        formatted = format_decimal(value, format='#,##0.00', locale='es_AR')
        return f"${formatted}"
    except:
        return f"${value:.2f}"


@app.route('/pagar_cuota/<int:cuota_id>', methods=['POST'])
def pagar_cuota(cuota_id):
    try:
        with db.session.begin_nested():  # Crear un savepoint
            # Obtener la cuota
            cuota = Cuota.query.get_or_404(cuota_id)

            # Verificar que la cuota no esté pagada
            if cuota.pagada:
                flash('Esta cuota ya está pagada', 'warning')
                return redirect(url_for('cuotas_a_vencer'))

            # Marcar la cuota como pagada
            cuota.pagada = True
            cuota.fecha_pago = datetime.now()
            cuota.monto_pagado = cuota.monto
            cuota.estado = 'PAGADA'

            # Actualizar el préstamo
            prestamo = cuota.prestamo
            prestamo.cuotas_pendientes -= 1
            prestamo.monto_adeudado -= cuota.monto

            # Si es la última cuota, actualizar estado del préstamo
            if prestamo.cuotas_pendientes == 0:
                prestamo.estado = 'FINALIZADO'
                prestamo.fecha_finalizacion = datetime.now()

            db.session.commit()
            flash('Cuota pagada exitosamente', 'success')

    except Exception as e:
        db.session.rollback()
        flash(f'Error al procesar el pago: {str(e)}', 'error')

    return redirect(url_for('cuotas_a_vencer'))


@app.route('/crear_cliente', methods=['POST'])
def crear_cliente():
    try:
        nuevo_cliente = Cliente(
            nombre=request.form['nombre'],
            apellido=request.form['apellido'],
            dni=request.form['dni'],
            telefono=request.form.get('telefono', ''),
            direccion=request.form.get('direccion', ''),
            correo_electronico=request.form.get('correo_electronico', '')
        )

        # Verificar si ya existe un cliente con el mismo DNI o correo
        cliente_existente = Cliente.query.filter(
            db.or_(
                Cliente.dni == nuevo_cliente.dni,
                Cliente.correo_electronico == nuevo_cliente.correo_electronico
            )
        ).first()

        if cliente_existente:
            flash('Ya existe un cliente con ese DNI o correo electrónico', 'error')
            return redirect(url_for('clientes'))

        db.session.add(nuevo_cliente)
        db.session.commit()
        flash('Cliente creado exitosamente', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al crear el cliente: {str(e)}', 'error')
    return redirect(url_for('clientes'))


@app.route('/prestamos')
def prestamos():
    # Modificar la consulta para ordenar por id_prestamo
    clientes = Cliente.query.options(
        db.joinedload(Cliente.prestamos).joinedload(Prestamo.cuotas)
    ).join(Cliente.prestamos).order_by(Prestamo.id_prestamo).all()
    
    return render_template('prestamos.html', clientes=clientes, active_page='prestamos')


@app.route('/crear_prestamo', methods=['POST'])
def crear_prestamo():
    try:
        # Obtener datos del formulario
        id_cliente = int(request.form['id_cliente'])
        monto_prestado = float(request.form['monto'])
        tasa_interes = float(request.form['tasa_interes'])
        cuotas_totales = int(request.form['cuotas'])
        
        # Verificar si hay garante
        tiene_garante = 'tiene_garante' in request.form and request.form['tiene_garante'] == 'on'
        id_garante = None

        if tiene_garante:
            try:
                # Crear o buscar garante solo si se marcó la opción
                dni_garante = request.form.get('dni_garante')
                if dni_garante:
                    garante = Garante.query.filter_by(dni=dni_garante).first()
                    if not garante:
                        garante = Garante(
                            nombre=request.form.get('nombre_garante', ''),
                            apellido=request.form.get('apellido_garante', ''),
                            dni=dni_garante,
                            telefono=request.form.get('telefono_garante', ''),
                            correo_electronico=request.form.get('correo_garante', ''),
                            direccion=request.form.get('direccion_garante', ''),
                            documentacion_verificada=True,
                            activo=True
                        )
                        db.session.add(garante)
                        db.session.flush()
                    id_garante = garante.id_garante
            except Exception as e:
                print(f"Error al procesar garante: {str(e)}")
                id_garante = None

        # Convertir la fecha de inicio del string a objeto datetime
        fecha_inicio = datetime.strptime(request.form['fecha_inicio'], '%Y-%m-%d')
        hoy = datetime.now()

        # Calcular fecha primer vencimiento (día 10 del mes siguiente)
        if fecha_inicio.month == 12:
            primer_vencimiento = datetime(fecha_inicio.year + 1, 1, 10)
        else:
            primer_vencimiento = datetime(fecha_inicio.year, fecha_inicio.month + 1, 10)

        # Calcular montos
        monto_total = monto_prestado * (1 + tasa_interes/100)
        monto_cuota = round(monto_total / cuotas_totales, 2)

        # Crear el préstamo primero y asegurarse de que se guarde
        nuevo_prestamo = Prestamo(
            id_cliente=id_cliente,
            id_garante=id_garante,  # Puede ser None
            monto_prestado=monto_prestado,
            tasa_interes=tasa_interes,
            cuotas_totales=cuotas_totales,
            cuotas_pendientes=cuotas_totales,
            monto_cuotas=monto_cuota,
            monto_adeudado=monto_total,
            fecha_inicio=fecha_inicio,
            fecha_finalizacion=primer_vencimiento + relativedelta(months=cuotas_totales-1),
            estado='ACTIVO'
        )

        db.session.add(nuevo_prestamo)
        db.session.flush()  # Asegurarse de que el préstamo tenga ID antes de crear las cuotas

        # Verificar que el préstamo tiene ID
        if not nuevo_prestamo.id_prestamo:
            raise ValueError("Error al generar ID del préstamo")

        # Usar la fecha de primera cuota del formulario
        fecha_primera_cuota = datetime.strptime(request.form['fecha_primera_cuota'], '%Y-%m-%d')
        dia_vencimiento = fecha_primera_cuota.day
        
        # Crear las cuotas
        hoy = datetime.now().date()
        cuotas_pagadas = 0
        monto_pagado = 0

        for i in range(nuevo_prestamo.cuotas_totales):
            # Calcular fecha de vencimiento manteniendo el mismo día
            if i == 0:
                fecha_vencimiento = fecha_primera_cuota
            else:
                # Usar relativedelta para mantener el mismo día del mes
                fecha_vencimiento = fecha_primera_cuota + relativedelta(months=i)
                # Asegurar que se mantenga el día de vencimiento
                fecha_vencimiento = fecha_vencimiento.replace(day=dia_vencimiento)
            
            # Verificar si la cuota ya venció
            esta_pagada = fecha_vencimiento.date() < hoy
            
            nueva_cuota = Cuota(
                id_prestamo=nuevo_prestamo.id_prestamo,
                numero_cuota=i + 1,
                fecha_vencimiento=fecha_vencimiento,
                monto=nuevo_prestamo.monto_cuotas,
                monto_pagado=nuevo_prestamo.monto_cuotas if esta_pagada else 0.0,
                pagada=esta_pagada,
                estado='PAGADA' if esta_pagada else 'PENDIENTE',
                fecha_pago=datetime.now() if esta_pagada else None
            )
            
            if esta_pagada:
                cuotas_pagadas += 1
                monto_pagado += nuevo_prestamo.monto_cuotas
            
            db.session.add(nueva_cuota)

        # Actualizar el préstamo con las cuotas pagadas
        nuevo_prestamo.cuotas_pendientes = nuevo_prestamo.cuotas_totales - cuotas_pagadas
        nuevo_prestamo.monto_adeudado = nuevo_prestamo.monto_adeudado - monto_pagado

        # Si todas las cuotas están pagadas, marcar el préstamo como finalizado
        if cuotas_pagadas == nuevo_prestamo.cuotas_totales:
            nuevo_prestamo.estado = 'FINALIZADO'
            nuevo_prestamo.fecha_finalizacion = datetime.now()

        db.session.commit()
        flash('Préstamo creado exitosamente', 'success')

    except Exception as e:
        db.session.rollback()
        flash(f'Error al crear el préstamo: {str(e)}', 'error')
        print(f"Error detallado: {str(e)}")  # Para debugging

    return redirect(url_for('prestamos'))


@app.route('/debug_db')
def debug_db():
    with app.app_context():
        cuotas = Cuota.query.all()
        prestamos = Prestamo.query.all()
        clientes = Cliente.query.all()

        debug_info = f"""
        Base de datos en: {os.path.abspath('instance/prestamos.db')}
        Total Cuotas: {len(cuotas)}
        Total Préstamos: {len(prestamos)}
        Total Clientes: {len(clientes)}
        
        Cuotas:
        {[f'ID: {c.id_cuota}, Vence: {c.fecha_vencimiento}, Pagada: {c.pagada}' for c in cuotas]}
        """

        return f"<pre>{debug_info}</pre>"


@app.route('/reset_prestamos')
def reset_prestamos():
    with app.app_context():
        try:
            # Eliminar todas las cuotas
            Cuota.query.delete()
            # Eliminar todos los préstamos
            Prestamo.query.delete()
            db.session.commit()
            return "Préstamos y cuotas eliminados correctamente"
        except Exception as e:
            db.session.rollback()
            return f"Error: {str(e)}"


@app.route('/debug_prestamo/<int:prestamo_id>')
def debug_prestamo(prestamo_id):
    prestamo = Prestamo.query.get_or_404(prestamo_id)
    cuotas = Cuota.query.filter_by(id_prestamo=prestamo_id).all()

    debug_info = f"""
    Préstamo ID: {prestamo.id_prestamo}
    Monto: ${prestamo.monto_prestado}
    Cuotas totales: {prestamo.cuotas_totales}
    Estado: {prestamo.estado}
    
    Cuotas:
    {[f'ID: {c.id_cuota}, Número: {c.numero_cuota}, Vence: {c.fecha_vencimiento}, Pagada: {c.pagada}' for c in cuotas]}
    """

    return f"<pre>{debug_info}</pre>"


@app.route('/recrear_cuotas/<int:prestamo_id>')
def recrear_cuotas(prestamo_id):
    try:
        prestamo = Prestamo.query.get_or_404(prestamo_id)

        # Eliminar cuotas existentes
        Cuota.query.filter_by(id_prestamo=prestamo_id).delete()

        # Crear nuevas cuotas
        fecha_base = prestamo.fecha_inicio or datetime.now()
        for i in range(prestamo.cuotas_totales):
            mes_actual = fecha_base.month + i
            año_actual = fecha_base.year + ((mes_actual - 1) // 12)
            mes_actual = ((mes_actual - 1) % 12) + 1

            fecha_vencimiento = fecha_base.replace(
                year=año_actual, month=mes_actual)

            nueva_cuota = Cuota(
                numero_cuota=i + 1,
                fecha_vencimiento=fecha_vencimiento,
                monto=prestamo.monto_cuotas,
                pagada=False,
                id_prestamo=prestamo_id
            )
            db.session.add(nueva_cuota)

        db.session.commit()
        return f"Cuotas recreadas exitosamente para el préstamo {prestamo_id}"

    except Exception as e:
        db.session.rollback()
        return f"Error: {str(e)}"


@app.route('/ver_cuotas/<int:prestamo_id>')
def ver_cuotas(prestamo_id):
    prestamo = Prestamo.query.get_or_404(prestamo_id)
    cuotas = Cuota.query.filter_by(
        id_prestamo=prestamo_id).order_by(Cuota.numero_cuota).all()

    debug_info = f"""
    Préstamo ID: {prestamo.id_prestamo}
    Cliente: {prestamo.cliente.apellido}, {prestamo.cliente.nombre}
    Monto: ${prestamo.monto_prestado:,.2f}
    Cuotas totales: {prestamo.cuotas_totales}
    Estado: {prestamo.estado}
    
    Detalle de Cuotas:
    """

    for cuota in cuotas:
        debug_info += f"""
        Cuota #{cuota.numero_cuota}:
        - ID: {cuota.id_cuota}
        - Vencimiento: {cuota.fecha_vencimiento.strftime('%d/%m/%Y')}
        - Monto: ${cuota.monto:,.2f}
        - Estado: {'PAGADA' if cuota.pagada else 'PENDIENTE'}
        """

    return f"<pre>{debug_info}</pre>"


@app.route('/consultar_bcra', methods=['GET', 'POST'])
def consultar_bcra():
    resultado = None
    resultado_cheques = None
    resultado_historico = None
    error = None

    if request.method == 'POST':
        try:
            identificacion = request.form.get('identificacion')
            if not identificacion:
                raise ValueError("Por favor ingrese una identificación")

            # Consulta deudas (principal)
            response = requests.get(BCRA_API_URL.format(identificacion), verify=False)
            
            if response.status_code != 200:
                raise Exception(f"Error en la consulta principal: {response.status_code}")

            # Consulta histórica
            response_historica = requests.get(BCRA_API_URL_HISTORICA.format(identificacion), verify=False)
            situacion_historica = None
            fecha_situacion = None
            
            if response_historica.status_code == 200:
                data_historica = response_historica.json()
                if 'results' in data_historica and 'periodos' in data_historica['results']:
                    # Buscar la situación 4 o 5 más reciente
                    for periodo in data_historica['results']['periodos']:
                        for entidad in periodo.get('entidades', []):
                            if entidad['situacion'] in [4, 5]:
                                # Convertir periodo (YYYYMM) a fecha
                                anio = int(periodo['periodo'][:4])
                                mes = int(periodo['periodo'][4:])
                                if not fecha_situacion or (anio, mes) > fecha_situacion:
                                    situacion_historica = entidad['situacion']
                                    fecha_situacion = (anio, mes)
                                    entidad_situacion = entidad['entidad']
                    
                    resultado_historico = {
                        'denominacion': data_historica['results'].get('denominacion', ''),
                        'identificacion': data_historica['results'].get('identificacion', ''),
                        'periodos': data_historica['results']['periodos']
                    }

            # Procesar datos de deudas actuales
            data = response.json()
            if 'results' in data and 'periodos' in data['results'] and data['results']['periodos']:
                todas_situacion_1 = True
                situaciones_encontradas = set()
                detalles = []

                ultimo_periodo = data['results']['periodos'][0]

                for entidad in ultimo_periodo.get('entidades', []):
                    if entidad['situacion'] != 1:
                        todas_situacion_1 = False
                        situaciones_encontradas.add(entidad['situacion'])

                    detalles.append({
                        'entidad': entidad['entidad'],
                        'situacion': entidad['situacion'],
                        'monto': entidad['monto'],
                        'fecha': entidad.get('fechaSit1', 'No disponible'),
                        'diasAtraso': entidad.get('diasAtrasoPago', 0),
                        'refinanciaciones': 'Sí' if entidad.get('refinanciaciones', False) else 'No',
                        'procesoJudicial': 'Sí' if entidad.get('procesoJud', False) else 'No'
                    })

                if todas_situacion_1:
                    estado = 'Preaprobado: Situación 1'
                    if situacion_historica:
                        estado += f' (Atención: Situación {situacion_historica} en {entidad_situacion} - {fecha_situacion[1]}/{fecha_situacion[0]})'
                    clase = 'warning' if situacion_historica else 'success'
                else:
                    situaciones = ', '.join(map(str, situaciones_encontradas))
                    estado = f'Revisar: Situación {situaciones}'
                    if situacion_historica:
                        estado += f' (Histórico: Situación {situacion_historica} en {entidad_situacion} - {fecha_situacion[1]}/{fecha_situacion[0]})'
                    clase = 'warning'

                resultado = {
                    'estado': estado,
                    'clase': clase,
                    'denominacion': data['results'].get('denominacion', ''),
                    'identificacion': data['results'].get('identificacion', ''),
                    'periodo': ultimo_periodo.get('periodo', ''),
                    'detalles': detalles
                }
            else:
                resultado = {
                    'estado': 'Sin deudas registradas',
                    'clase': 'success',
                    'denominacion': data['results'].get('denominacion', ''),
                    'identificacion': identificacion,
                    'periodo': 'No disponible',
                    'detalles': []
                }

            # Consulta cheques (secundaria)
            try:
                # Construir URL específica para cheques rechazados
                base_url = "https://api.bcra.gob.ar/centraldedeudores/v1.0/Deudas/"
                cheques_url = f"{base_url}ChequesRechazados/{identificacion}"
                print(f"URL de consulta cheques: {cheques_url}")  # Debug
                
                response_cheques = requests.get(cheques_url, verify=False)
                print(f"Status code cheques: {response_cheques.status_code}")  # Debug
                print(f"Respuesta completa: {response_cheques.text}")  # Debug
                
                if response_cheques.status_code == 200:
                    data_cheques = response_cheques.json()
                    print(f"Data cheques parseada: {data_cheques}")  # Debug
                    
                    # Verificar la estructura completa de la respuesta
                    if ('results' in data_cheques and 
                        'causales' in data_cheques['results'] and 
                        data_cheques['results']['causales']):
                        
                        cheques_detalles = []
                        for causal in data_cheques['results']['causales']:
                            print(f"Procesando causal: {causal}")  # Debug
                            
                            for entidad in causal.get('entidades', []):
                                print(f"Procesando entidad: {entidad}")  # Debug
                                
                                for detalle in entidad.get('detalle', []):
                                    print(f"Procesando detalle: {detalle}")  # Debug
                                    
                                    cheques_detalles.append({
                                        'entidad': entidad['entidad'],
                                        'causal': causal['causal'],
                                        'nroCheque': detalle['nroCheque'],
                                        'fechaRechazo': detalle['fechaRechazo'],
                                        'monto': detalle['monto'],
                                        'fechaPago': detalle.get('fechaPago', 'No Registra Pago'),
                                        'fechaPagoMulta': detalle.get('fechaPagoMulta', 'No disponible'),
                                        'estadoMulta': detalle.get('estadoMulta', 'No disponible'),
                                        'procesoJudicial': 'Sí' if detalle.get('procesoJud', False) else 'No'
                                    })

                        if cheques_detalles:
                            resultado_cheques = {
                                'denominacion': data_cheques['results'].get('denominacion', ''),
                                'identificacion': data_cheques['results'].get('identificacion', ''),
                                'detalles': cheques_detalles
                            }
                            print(f"Resultado cheques final: {resultado_cheques}")  # Debug
                        else:
                            print("No se encontraron detalles de cheques")  # Debug
                    else:
                        print("Estructura de respuesta inválida o sin datos de cheques")  # Debug
                        print(f"Estructura de data_cheques: {data_cheques}")  # Debug
                else:
                    print(f"Error en la consulta de cheques: Status {response_cheques.status_code}")
                    print(f"Respuesta de error: {response_cheques.text}")  # Debug
                
            except Exception as e:
                print(f"Error en consulta de cheques: {str(e)}")
                print(f"Tipo de error: {type(e)}")
                import traceback
                traceback.print_exc()  # Esto imprimirá el stack trace completo

        except ValueError as ve:
            error = str(ve)
        except requests.RequestException as e:
            error = f"Error de conexión: {str(e)}"
        except Exception as e:
            error = f"Error inesperado: {str(e)}"
            print(f"Error detallado: {str(e)}")

    return render_template('consulta_bcra.html', 
                         resultado=resultado, 
                         resultado_cheques=resultado_cheques,
                         resultado_historico=resultado_historico,
                         error=error,
                         active_page='bcra')


@app.route('/prestamos_otorgados', methods=['GET'])
def prestamos_otorgados():
    return render_template('prestamos_otorgados.html')


@app.route('/buscar_clientes')
def buscar_clientes():
    return render_template('buscar_clientes.html', active_page='cargar_prestamos')

@app.route('/api/buscar_clientes')
def api_buscar_clientes():
    query = request.args.get('query', '').strip()
    tipo_busqueda = request.args.get('tipo', 'todos')
    
    print(f"Búsqueda recibida - Query: '{query}', Tipo: '{tipo_busqueda}'")
    
    if not query:
        return jsonify([])
    
    try:
        # Simplificar la consulta para usar solo los campos que existen
        if tipo_busqueda == 'dni':
            clientes = Cliente.query.filter(Cliente.dni.ilike(f'%{query}%')).all()
        elif tipo_busqueda == 'apellido':
            clientes = Cliente.query.filter(Cliente.apellido.ilike(f'%{query}%')).all()
        else:  # 'todos'
            clientes = Cliente.query.filter(
                or_(
                    Cliente.dni.ilike(f'%{query}%'),
                    Cliente.apellido.ilike(f'%{query}%'),
                    Cliente.nombre.ilike(f'%{query}%')
                )
            ).all()
        
        # Simplificar el resultado para incluir solo los campos que existen
        resultado = [{
            'id_cliente': cliente.id_cliente,
            'nombre': cliente.nombre,
            'apellido': cliente.apellido,
            'dni': cliente.dni,
            'telefono': cliente.telefono or '-',
            'direccion': cliente.direccion or '-',
            'correo_electronico': cliente.correo_electronico or '-'
        } for cliente in clientes]
        
        print(f"Resultados encontrados: {len(resultado)}")
        return jsonify(resultado)
    
    except Exception as e:
        print(f"Error en búsqueda de clientes: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Error al buscar clientes: {str(e)}'}), 500
    
@app.route('/cargar_prestamo/<int:id_cliente>')
def cargar_prestamo(id_cliente):
    cliente = Cliente.query.get_or_404(id_cliente)
    return render_template('cargar_prestamo.html', cliente=cliente)

@app.route('/guardar_prestamo', methods=['POST'])
def guardar_prestamo():
    try:
        # Obtener datos del formulario
        id_cliente = request.form['id_cliente']
        monto_prestado = float(request.form['monto_prestado'])
        tasa_interes = float(request.form['tasa_interes'])
        cuotas_totales = int(request.form['cuotas_totales'])
        monto_cuotas = float(request.form['monto_cuotas'])
        monto_adeudado = float(request.form['monto_adeudado'])
        fecha_inicio = datetime.strptime(request.form['fecha_inicio'], '%Y-%m-%d')
        fecha_vencimiento_primera_cuota = datetime.strptime(request.form['fecha_vencimiento_primera_cuota'], '%Y-%m-%d')

        # Crear el préstamo
        nuevo_prestamo = Prestamo(
            id_cliente=id_cliente,
            monto_prestado=monto_prestado,
            tasa_interes=tasa_interes,
            cuotas_totales=cuotas_totales,
            cuotas_pendientes=cuotas_totales,
            monto_cuotas=monto_cuotas,
            monto_adeudado=monto_adeudado,
            fecha_inicio=fecha_inicio,
            fecha_finalizacion=None,
            estado='ACTIVO'
        )
        
        db.session.add(nuevo_prestamo)
        db.session.flush()  # Para obtener el id_prestamo

        # Crear las cuotas usando la fecha de vencimiento de la primera cuota
        fecha_actual = datetime.now().date()
        fecha_primera_cuota = fecha_vencimiento_primera_cuota.date()
        
        cuotas_pagadas = 0
        monto_pagado = 0
        
        for i in range(cuotas_totales):
            fecha_vencimiento = fecha_primera_cuota + relativedelta(months=i)
            
            # Determinar si la cuota ya está vencida
            esta_pagada = fecha_vencimiento < fecha_actual
            
            cuota = Cuota(
                id_prestamo=nuevo_prestamo.id_prestamo,
                numero_cuota=i + 1,
                monto=monto_cuotas,
                fecha_vencimiento=fecha_vencimiento,
                estado='PAGADA' if esta_pagada else 'PENDIENTE',
                monto_pagado=monto_cuotas if esta_pagada else 0,
                pagada=esta_pagada,
                fecha_pago=datetime.now() if esta_pagada else None
            )
            
            if esta_pagada:
                cuotas_pagadas += 1
                monto_pagado += monto_cuotas
            
            db.session.add(cuota)

        # Actualizar el préstamo con las cuotas pagadas
        nuevo_prestamo.cuotas_pendientes = cuotas_totales - cuotas_pagadas
        nuevo_prestamo.monto_adeudado = monto_adeudado - monto_pagado

        # Procesar garante si está incluido
        if 'tiene_garante' in request.form:
            # Verificar si ya existe un garante con ese DNI
            dni_garante = request.form['dni_garante']
            garante = Garante.query.filter_by(dni=dni_garante).first()

            if not garante:
                # Crear nuevo garante
                garante = Garante(
                    nombre=request.form['nombre_garante'],
                    apellido=request.form['apellido_garante'],
                    dni=dni_garante,
                    telefono=request.form.get('telefono_garante', ''),
                    correo_electronico=request.form.get('correo_garante', ''),
                    direccion=request.form.get('direccion_garante', ''),
                    documentacion_verificada=True,
                    activo=True
                )
                db.session.add(garante)
                db.session.flush()  # Para obtener el id_garante

            id_garante = garante.id_garante

            # Actualizar el préstamo con el nuevo garante
            nuevo_prestamo.id_garante = id_garante

        db.session.commit()
        flash('Préstamo guardado exitosamente', 'success')
        return redirect(url_for('prestamos'))

    except Exception as e:
        db.session.rollback()
        flash(f'Error al guardar el préstamo: {str(e)}', 'error')
        return redirect(url_for('prestamos'))


@app.route('/eliminar_cliente/<int:id>', methods=['POST'])
def eliminar_cliente(id):
    app.logger.info(f'Iniciando eliminación del cliente {id}')
    
    try:
        cliente = Cliente.query.get_or_404(id)
        app.logger.info(f'Cliente encontrado: {cliente.nombre} {cliente.apellido}')
        
        # Obtener y contar préstamos
        prestamos = Prestamo.query.filter_by(id_cliente=id).all()
        app.logger.info(f'Préstamos encontrados: {len(prestamos)}')
        
        # Para cada préstamo, eliminar sus cuotas
        for prestamo in prestamos:
            cuotas = Cuota.query.filter_by(id_prestamo=prestamo.id_prestamo).all()
            app.logger.info(f'Cuotas encontradas para préstamo {prestamo.id_prestamo}: {len(cuotas)}')
            Cuota.query.filter_by(id_prestamo=prestamo.id_prestamo).delete()
        
        # Eliminar préstamos
        Prestamo.query.filter_by(id_cliente=id).delete()
        
        # Eliminar cliente
        db.session.delete(cliente)
        db.session.commit()
        
        app.logger.info('Eliminación completada exitosamente')
        flash(f'Cliente {cliente.nombre} {cliente.apellido} y todos sus datos relacionados han sido eliminados correctamente', 'success')
        
    except Exception as e:
        db.session.rollback()
        app.logger.error(f'Error durante la eliminación: {str(e)}')
        flash(f'Error al eliminar el cliente: {str(e)}', 'error')
        
    return redirect(url_for('clientes'))


@app.route('/debug_schema')
def debug_schema():
    try:
        inspector = inspect(db.engine)
        
        html = '<h2>Estructura de la Base de Datos</h2>'
        
        # Obtener todas las tablas
        for table_name in inspector.get_table_names():
            html += f'<h3>Tabla: {table_name}</h3>'
            html += '<table border="1" style="border-collapse: collapse; margin-bottom: 20px;">'
            html += '''
                <tr>
                    <th style="padding: 8px;">Columna</th>
                    <th style="padding: 8px;">Tipo</th>
                    <th style="padding: 8px;">Nullable</th>
                    <th style="padding: 8px;">Default</th>
                    <th style="padding: 8px;">Primary Key</th>
                    <th style="padding: 8px;">Foreign Key</th>
                </tr>
            '''
            
            # Obtener columnas de la tabla
            columns = inspector.get_columns(table_name)
            for column in columns:
                # Verificar si es foreign key
                fk = ''
                for fk_data in inspector.get_foreign_keys(table_name):
                    if column['name'] in fk_data['constrained_columns']:
                        fk = f"-> {fk_data['referred_table']}.{fk_data['referred_columns'][0]}"
                
                html += f'''
                    <tr>
                        <td style="padding: 8px;">{column['name']}</td>
                        <td style="padding: 8px;">{column['type']}</td>
                        <td style="padding: 8px;">{column['nullable']}</td>
                        <td style="padding: 8px;">{column.get('default', '')}</td>
                        <td style="padding: 8px;">{'Yes' if column.get('primary_key', False) else 'No'}</td>
                        <td style="padding: 8px;">{fk}</td>
                    </tr>
                '''
            
            html += '</table>'
            
            # Mostrar índices
            indices = inspector.get_indexes(table_name)
            if indices:
                html += '<h4>Índices:</h4>'
                html += '<ul>'
                for index in indices:
                    html += f'''
                        <li>
                            {index['name']}: {', '.join(index['column_names'])}
                            {'(único)' if index['unique'] else ''}
                        </li>
                    '''
                html += '</ul>'
        
        return html
    except Exception as e:
        return f'Error al inspeccionar la base de datos: {str(e)}'
    
@app.route('/cleanup_db')
def cleanup_db():
    try:
        with db.engine.connect() as conn:
            # Desactivar temporalmente las restricciones de clave foránea
            conn.execute(text("PRAGMA foreign_keys = OFF"))

            # Eliminar en orden correcto (primero las tablas hijas)
            conn.execute(text("DELETE FROM cuota"))
            conn.execute(text("DELETE FROM prestamo"))
            conn.execute(text("DELETE FROM cliente"))
            conn.execute(text("DELETE FROM garante"))
            
            # Reactivar las restricciones de clave foránea
            conn.execute(text("PRAGMA foreign_keys = ON"))
            
            # Confirmar los cambios
            conn.commit()
            
            return "Limpieza de base de datos completada exitosamente"
            
    except Exception as e:
        return f"Error limpiando la base de datos: {str(e)}"

def init_db():
    """Función para inicializar/verificar la base de datos"""
    print("Iniciando verificación de la base de datos...")
    
    # db_path = 'instance/prestamos.db'
    
    try:
        # Verificar si las tablas existen usando la sintaxis moderna
        with app.app_context():
            with db.engine.connect() as conn:
                # Intentar hacer una consulta simple para verificar si la DB existe y tiene la estructura correcta
                conn.execute(text("SELECT 1 FROM cliente"))
                print("Base de datos existente verificada correctamente!")
                
    except Exception as e:
        print(f"La base de datos necesita ser inicializada: {str(e)}")
        
        with app.app_context():
            # Crear directorio instance si no existe
            if not os.path.exists('instance'):
                print("Creando directorio instance...")
                os.makedirs('instance')
            
            print("Creando nuevas tablas...")
            db.create_all()
            print("Base de datos inicializada exitosamente!")

@app.route('/actualizar_estado_cuota', methods=['POST'])
def actualizar_estado_cuota():
    try:
        data = request.get_json()
        id_cuota = data.get('id_cuota')
        pagada = data.get('pagada')

        # Cambiar query.get() por db.session.get()
        cuota = db.session.get(Cuota, id_cuota)
        
        if cuota:
            cuota.pagada = pagada
            cuota.estado = 'PAGADA' if pagada else 'PENDIENTE'
            db.session.commit()
            return jsonify({'success': True})
        return jsonify({'success': False, 'error': 'Cuota no encontrada'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)})

@app.route('/buscar_garante/<dni>')
def buscar_garante(dni):
    garante = Garante.query.filter_by(dni=dni).first()
    
    if garante:
        return jsonify({
            'encontrado': True,
            'garante': {
                'nombre': garante.nombre,
                'apellido': garante.apellido,
                'telefono': garante.telefono,
                'correo_electronico': garante.correo_electronico,
                'direccion': garante.direccion
            }
        })
    else:
        return jsonify({
            'encontrado': False
        })

@app.route('/admin')
def admin():
    # Obtener todos los datos de cada tabla
    clientes = Cliente.query.all()
    prestamos = Prestamo.query.all()
    cuotas = Cuota.query.all()
    garantes = Garante.query.all()

    return render_template('admin.html', 
                         clientes=clientes,
                         prestamos=prestamos,
                         cuotas=cuotas,
                         garantes=garantes)

@app.route('/test_bcra/<cuit>')
def test_bcra(cuit):
    try:
        # Construir la URL con el CUIT
        url = BCRA_API_URL.format(cuit)
        
        # Realizar la consulta
        response = requests.get(url, verify=False)
        
        # Obtener el JSON completo
        data = response.json()
        
        # Formatear la respuesta para mejor legibilidad
        formatted_response = {
            'status_code': response.status_code,
            'headers': dict(response.headers),
            'raw_data': data
        }
        
        # Retornar como HTML preformateado para mejor visualización
        return f'<pre>{json.dumps(formatted_response, indent=2, ensure_ascii=False)}</pre>'
        
    except Exception as e:
        return f'Error: {str(e)}\n\nStack trace:\n{traceback.format_exc()}'

@app.route('/actualizar_fechas_prestamo/<int:id_prestamo>', methods=['GET', 'POST'])
def actualizar_fechas_prestamo(id_prestamo):
    prestamo = Prestamo.query.get_or_404(id_prestamo)
    
    if request.method == 'GET':
        # Mostrar página de confirmación
        return render_template('confirmar_actualizacion.html', 
                            prestamo=prestamo,
                            nueva_fecha_primera_cuota="10/04/2024",
                            nueva_fecha_final="10/03/2025")
    
    try:
        # Obtener la nueva fecha de primera cuota
        nueva_fecha_primera_cuota = datetime(2024, 4, 10)  # 10/04/2024
        
        # Actualizar todas las cuotas
        cuotas = Cuota.query.filter_by(id_prestamo=id_prestamo).order_by(Cuota.numero_cuota).all()
        
        for i, cuota in enumerate(cuotas):
            # Calcular la nueva fecha de vencimiento para cada cuota
            nueva_fecha = nueva_fecha_primera_cuota + relativedelta(months=i)
            cuota.fecha_vencimiento = nueva_fecha
            
            # Establecer todas las cuotas como PENDIENTES
            cuota.estado = 'PENDIENTE'
            cuota.pagada = False
            cuota.monto_pagado = 0
            cuota.fecha_pago = None
        
        # Actualizar la fecha de finalización del préstamo
        prestamo.fecha_finalizacion = nueva_fecha_primera_cuota + relativedelta(months=len(cuotas)-1)
        
        # Actualizar el préstamo
        prestamo.cuotas_pendientes = len(cuotas)  # Todas las cuotas pendientes
        prestamo.monto_adeudado = sum(cuota.monto for cuota in cuotas)  # Todo el monto pendiente
        
        db.session.commit()
        flash('Fechas del préstamo actualizadas correctamente', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error al actualizar las fechas: {str(e)}', 'error')
    
    return redirect(url_for('prestamos'))

@app.route('/generar_contrato/<int:prestamo_id>')
def generar_contrato(prestamo_id):
    try:
        # Intentar configurar el locale para español
        try:
            locale.setlocale(locale.LC_ALL, 'es_ES.UTF-8')
        except locale.Error:
            try:
                locale.setlocale(locale.LC_ALL, 'es_ES')
            except locale.Error:
                try:
                    locale.setlocale(locale.LC_ALL, 'Spanish_Spain.1252')
                except locale.Error:
                    # Si ningún locale español está disponible, usar el locale por defecto
                    locale.setlocale(locale.LC_ALL, '')
        
        # Obtener datos
        prestamo = Prestamo.query.get_or_404(prestamo_id)
        cliente = prestamo.cliente
        garante = Garante.query.get(prestamo.id_garante) if prestamo.id_garante else None
        
        # Formatear números manualmente si el locale falla
        def format_money(amount):
            """Formatea números en formato español manualmente"""
            return "{:,.2f}".format(amount).replace(",", "X").replace(".", ",").replace("X", ".")
        
        # Cargar el template
        doc = Document('templates/template_mutuo.docx')
        
        # Crear diccionario con todos los reemplazos
        replacements = {
            '{fecha_actual}': datetime.now().strftime('%d/%m/%Y'),
            '{nombre_apellido}': f"{cliente.nombre} {cliente.apellido}",
            '{dni}': cliente.dni,
            '{domicilio}': cliente.direccion or '',
            '{monto_prestado}': f"${format_money(prestamo.monto_prestado)}",
            '{monto_prestado_letras}': numero_a_letras(prestamo.monto_prestado),
            '{cantidad_cuotas}': str(prestamo.cuotas_totales),
            '{monto_cuota}': f"${format_money(prestamo.monto_cuotas)}",
            '{monto_cuota_letras}': numero_a_letras(prestamo.monto_cuotas),
            '{fecha_primera_cuota}': prestamo.cuotas[0].fecha_vencimiento.strftime('%d/%m/%Y'),
        }
        
        if garante:
            replacements.update({
                '{nombre_apellido_garante}': f"{garante.nombre} {garante.apellido}",
                '{dni_garante}': garante.dni,
                '{domicilio_garante}': garante.direccion or '',
            })
        
        # Reemplazar en el documento
        for paragraph in doc.paragraphs:
            for key, value in replacements.items():
                if key in paragraph.text:
                    paragraph.text = paragraph.text.replace(key, value)
        
        # Guardar temporalmente
        temp_path = f'prestamos_app/temp/contrato_prestamo_{prestamo_id}.docx'
        os.makedirs('prestamos_app/temp', exist_ok=True)
        doc.save(temp_path)
        
        # Enviar archivo
        return send_file(
            temp_path,
            as_attachment=True,
            download_name=f'Contrato_Prestamo_{cliente.apellido}_{prestamo_id}.docx'
        )
        
    except Exception as e:
        print(f"Error detallado: {str(e)}")  # Para debugging
        flash(f'Error al generar el contrato: {str(e)}', 'error')
        return redirect(url_for('prestamos'))

def numero_a_letras(numero):
    # Implementar función para convertir números a letras
    # Puedes usar la biblioteca num2words
    from num2words import num2words
    return num2words(numero, lang='es').upper()

if __name__ == '__main__':
    print("Iniciando servidor de desarrollo...")
    app.run(debug=True)
else:
    # En producción, no intentar iniciar el servidor
    print("Iniciando en modo producción")


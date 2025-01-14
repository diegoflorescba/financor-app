from flask import Flask, render_template, request, redirect, url_for, flash, send_file, jsonify
from datetime import datetime, date, timedelta
from calendar import monthrange
from dateutil.relativedelta import relativedelta
from models import db, Cliente, Prestamo, Cuota
import os
import pandas as pd
import io
import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning
from sqlalchemy import or_
import locale


app = Flask(__name__)

# Suprimir advertencias de SSL inseguro
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

# Configuración
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///prestamos.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'tu_clave_secreta'

# Inicializar la base de datos con la app
db.init_app(app)

# Crear todas las tablas
with app.app_context():
    print("Iniciando creación de base de datos...")

    # Verificar si el archivo de base de datos existe y eliminarlo
    db_path = 'instance/prestamos.db'
    if not os.path.exists(db_path):
        print("Creando todas las tablas...")
        db.create_all()

        print("Verificando estructura de las tablas...")
        # Imprimir todas las tablas creadas
        for table in db.metadata.tables.keys():
            print(f"Tabla creada: {table}")
            # Imprimir columnas de cada tabla
            for column in db.metadata.tables[table].columns:
                print(f"  - Columna: {column.name}, Tipo: {column.type}")

print("Inicialización de la base de datos completada")

# Agregar este código para debug
db_path = os.path.abspath('instance/prestamos.db')
print(f"Ruta completa de la base de datos: {db_path}")
print(f"¿Existe el archivo?: {os.path.exists(db_path)}")

# Configuración de la API BCRA
BCRA_API_URL = "https://api.bcra.gob.ar/centraldedeudores/v1.0/Deudas/{}"


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/clientes')
def clientes():
    clientes_list = Cliente.query.order_by(Cliente.apellido).all()
    return render_template('clientes.html', clientes=clientes_list)


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

    return render_template('cliente_nuevo.html', datetime=datetime)


@app.route('/registro', methods=['GET', 'POST'])
def registro():
    form_data = {}
    errors = {}

    if request.method == 'POST':
        try:
            # Capturar todos los datos del formulario
            form_data = {
                'nombre': request.form['nombre'].upper(),
                'apellido': request.form['apellido'].upper(),
                'dni': request.form['dni'],
                'direccion': request.form['direccion'],
                'telefono': request.form['telefono'],
                'correo_electronico': request.form['correo_electronico'],
                'documentacion_verificada': request.form.get('documentacion_verificada') == 'on',
                'tiene_prestamo': request.form.get('tiene_prestamo') == 'on'
            }

            # Verificar DNI y correo electrónico duplicados
            cliente_existente = Cliente.query.filter(
                or_(
                    Cliente.dni == form_data['dni'],
                    Cliente.correo_electronico == form_data['correo_electronico']
                )
            ).first()

            if cliente_existente:
                if cliente_existente.dni == form_data['dni']:
                    errors['dni'] = 'Ya existe un cliente registrado con este DNI'
                if cliente_existente.correo_electronico == form_data['correo_electronico']:
                    errors['correo_electronico'] = 'Ya existe un cliente registrado con este correo electrónico'
                return render_template('registro.html', form_data=form_data, errors=errors)

            # Si no hay errores, proceder con el registro
            nuevo_cliente = Cliente(
                nombre=form_data['nombre'],
                apellido=form_data['apellido'],
                dni=form_data['dni'],
                direccion=form_data['direccion'],
                telefono=form_data['telefono'],
                correo_electronico=form_data['correo_electronico'],
                documentacion_verificada=form_data['documentacion_verificada'],
                fecha_registro=datetime.now(),
                activo=True
            )
            db.session.add(nuevo_cliente)
            db.session.flush()

            if form_data['tiene_prestamo']:
                nuevo_prestamo = Prestamo(
                    id_cliente=nuevo_cliente.id_cliente,
                    monto_prestado=float(form_data['monto']),
                    tasa_interes=float(form_data['interes']),
                    cuotas_totales=int(form_data['cuotas_totales']),
                    cuotas_pendientes=int(form_data['cuotas_pendientes']),
                    monto_cuotas=float(form_data['monto_cuotas']),
                    monto_adeudado=float(form_data['monto_adeudado']),
                    fecha_inicio=datetime.strptime(
                        form_data['fecha_inicio'], '%Y-%m-%d').date(),
                    fecha_vencimiento=datetime.strptime(
                        form_data['fecha_finalizacion'], '%Y-%m-%d').date()
                )
                db.session.add(nuevo_prestamo)

            db.session.commit()
            flash('Cliente registrado exitosamente', 'success')
            return redirect(url_for('registro'))

        except Exception as e:
            db.session.rollback()
            flash(f'Error al procesar la solicitud: {str(e)}', 'error')
            return render_template('registro.html', form_data=form_data, errors=errors)

    return render_template('registro.html', form_data={}, errors={})


@app.route('/reportes')
def reportes():
    # Configurar el locale en español
    locale.setlocale(locale.LC_TIME, 'es_ES.UTF-8')
    
    # Obtener todos los préstamos activos
    prestamos = Prestamo.query.filter(
        Prestamo.estado == 'ACTIVO',
        Prestamo.monto_adeudado > 0
    ).all()
    
    # Calcular el total adeudado general
    total_adeudado = sum(prestamo.monto_adeudado for prestamo in prestamos)
    
    # Obtener el mes actual
    mes_actual = datetime.now()
    
    # Calcular el adeudado del mes actual (cuotas pendientes de este mes)
    adeudado_mes_actual = db.session.query(db.func.sum(Cuota.monto))\
        .join(Prestamo)\
        .filter(
            Prestamo.estado == 'ACTIVO',
            Cuota.estado == 'PENDIENTE',
            db.extract('month', Cuota.fecha_vencimiento) == mes_actual.month,
            db.extract('year', Cuota.fecha_vencimiento) == mes_actual.year
        ).scalar() or 0.0
    
    # Formatear la fecha en español
    mes_actual_str = mes_actual.strftime('%B %Y').capitalize()
    
    return render_template('reportes.html',
                         prestamos=prestamos,
                         mes_actual=mes_actual_str,
                         total_adeudado=total_adeudado,
                         adeudado_mes_actual=adeudado_mes_actual)


@app.route('/cuotas_a_vencer')
def cuotas_a_vencer():
    today = date.today()
    # Obtener el último día del mes actual
    _, ultimo_dia = monthrange(today.year, today.month)
    
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
                         today=today,
                         mes_actual=today.strftime('%B %Y'),
                         total_a_cobrar=total_a_cobrar)


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
            cliente.correo_electronico = request.form.get('correo_electronico', '')
            cliente.direccion = request.form.get('direccion', '')

            db.session.commit()
            flash('Cliente actualizado exitosamente', 'success')
            return redirect(url_for('clientes'))

        except Exception as e:
            db.session.rollback()
            flash(f'Error al actualizar el cliente: {str(e)}', 'error')

    return render_template('cliente_editar.html', cliente=cliente)


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
                'Estado': 'Pendiente' if not cuota.pagada else 'Pagada'
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
                prestamo.fecha_vencimiento = datetime.now()

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
    # Obtener todos los clientes con sus préstamos y cuotas precargados
    clientes = Cliente.query.options(
        db.joinedload(Cliente.prestamos).joinedload(Prestamo.cuotas)
    ).order_by(Cliente.apellido).all()
    
    return render_template('prestamos.html', clientes=clientes)


@app.route('/crear_prestamo', methods=['POST'])
def crear_prestamo():
    try:
        # Obtener datos del formulario
        id_cliente = int(request.form['id_cliente'])
        monto_prestado = float(request.form['monto'])
        tasa_interes = float(request.form['tasa_interes'])
        cuotas_totales = int(request.form['cuotas'])

        # Calcular fecha primer vencimiento (día 10 del mes siguiente)
        hoy = datetime.now()
        if hoy.month == 12:
            primer_vencimiento = datetime(hoy.year + 1, 1, 10)
        else:
            primer_vencimiento = datetime(hoy.year, hoy.month + 1, 10)

        # Calcular montos
        monto_total = monto_prestado * (1 + tasa_interes/100)
        monto_cuota = round(monto_total / cuotas_totales, 2)

        # Calcular fecha de vencimiento final del préstamo
        fecha_vencimiento_final = primer_vencimiento + relativedelta(months=cuotas_totales-1)

        # Crear el préstamo
        nuevo_prestamo = Prestamo(
            id_cliente=id_cliente,
            monto_prestado=monto_prestado,
            tasa_interes=tasa_interes,
            cuotas_totales=cuotas_totales,
            cuotas_pendientes=cuotas_totales,
            monto_cuotas=monto_cuota,
            monto_adeudado=monto_total,
            fecha_inicio=hoy,
            fecha_vencimiento=fecha_vencimiento_final,
            estado='ACTIVO'
        )

        db.session.add(nuevo_prestamo)
        db.session.flush()

        # Crear las cuotas
        for i in range(cuotas_totales):
            if i == 0:
                fecha_vencimiento = primer_vencimiento
            else:
                fecha_vencimiento = primer_vencimiento + relativedelta(months=i)

            nueva_cuota = Cuota(
                numero_cuota=i + 1,
                fecha_vencimiento=fecha_vencimiento,
                monto=monto_cuota,
                monto_pagado=0.0,
                pagada=False,
                estado='PENDIENTE',
                id_prestamo=nuevo_prestamo.id_prestamo
            )

            db.session.add(nueva_cuota)

        db.session.commit()
        flash('Préstamo creado exitosamente', 'success')

    except Exception as e:
        db.session.rollback()
        flash(f'Error al crear el préstamo: {str(e)}', 'error')

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
        - Estado: {'Pagada' if cuota.pagada else 'Pendiente'}
        """

    return f"<pre>{debug_info}</pre>"


@app.route('/consultar_bcra', methods=['GET', 'POST'])
def consultar_bcra():
    resultado = None
    resultado_cheques = None
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

            # Procesar datos de deudas
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
                    clase = 'success'
                else:
                    situaciones = ', '.join(map(str, situaciones_encontradas))
                    estado = f'Revisar: Situación {situaciones}'
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
                         error=error)


@app.route('/prestamos_otorgados', methods=['GET'])
def prestamos_otorgados():
    return render_template('prestamos_otorgados.html')


@app.route('/buscar_clientes')
def buscar_clientes():
    return render_template('buscar_clientes.html')

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
        fecha_inicio = datetime.strptime(request.form['fecha_inicio'], '%Y-%m-%d')
        fecha_actual = datetime.now()
        
        nuevo_prestamo = Prestamo(
            id_cliente=request.form['id_cliente'],
            monto_prestado=float(request.form['monto_prestado']),
            tasa_interes=float(request.form['tasa_interes']),
            cuotas_totales=int(request.form['cuotas_totales']),
            cuotas_pendientes=int(request.form['cuotas_totales']),
            monto_cuotas=float(request.form['monto_cuotas']),
            monto_adeudado=float(request.form['monto_adeudado']),
            fecha_inicio=fecha_inicio,
            fecha_vencimiento=datetime.strptime(request.form['fecha_vencimiento'], '%Y-%m-%d'),
            estado='ACTIVO'
        )

        db.session.add(nuevo_prestamo)
        db.session.flush()  # Para obtener el id_prestamo

        # Generar las cuotas
        monto_cuota = float(request.form['monto_cuotas'])
        cuotas_pagadas = 0
        for i in range(int(request.form['cuotas_totales'])):
            fecha_vencimiento = fecha_inicio + relativedelta(months=i+1)
            
            # Determinar si la cuota está vencida
            esta_pagada = fecha_vencimiento.date() < fecha_actual.date()
            
            nueva_cuota = Cuota(
                id_prestamo=nuevo_prestamo.id_prestamo,
                numero_cuota=i + 1,
                fecha_vencimiento=fecha_vencimiento,
                monto=monto_cuota,
                monto_pagado=monto_cuota if esta_pagada else 0.0,
                pagada=esta_pagada,
                estado='PAGADA' if esta_pagada else 'PENDIENTE',
                fecha_pago=fecha_actual if esta_pagada else None
            )
            
            if esta_pagada:
                cuotas_pagadas += 1
            
            db.session.add(nueva_cuota)

        # Actualizar el préstamo con las cuotas pagadas
        nuevo_prestamo.cuotas_pendientes -= cuotas_pagadas
        nuevo_prestamo.monto_adeudado = monto_cuota * (nuevo_prestamo.cuotas_pendientes)

        db.session.commit()

        # Obtener información del cliente para el mensaje
        cliente = Cliente.query.get(request.form['id_cliente'])
        flash(f'Préstamo registrado exitosamente para {cliente.nombre} {cliente.apellido}', 'success')
        return redirect(url_for('buscar_clientes'))

    except Exception as e:
        db.session.rollback()
        flash(f'Error al registrar el préstamo: {str(e)}', 'error')
        return redirect(url_for('cargar_prestamo', id_cliente=request.form['id_cliente']))

if __name__ == '__main__':
    app.run(debug=True)

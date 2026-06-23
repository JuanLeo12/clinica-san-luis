import sqlite3

conn = sqlite3.connect('clinic_app.sqlite3')
conn.text_factory = str

def transfer_data(old_table, new_table, columns_map):
    """Transfer data from old table to new table with French column names"""
    cols = ', '.join(columns_map.keys())
    placeholders = ', '.join(['?' for _ in columns_map])

    cursor = conn.execute(f'SELECT * FROM {old_table}')
    rows = cursor.fetchall()

    if not rows:
        return 0

    source_cols = [desc[0] for desc in cursor.description]
    indices = [source_cols.index(old_col) for old_col in columns_map.values() if old_col in source_cols]

    inserted = 0
    for row in rows:
        new_row = tuple(row[i] for i in indices)
        try:
            conn.execute(f'INSERT INTO {new_table} ({cols}) VALUES ({placeholders})', new_row)
            inserted += 1
        except Exception as e:
            print(f'Error: {e}')

    return inserted

print('1. PACIENTES')
conn.execute('''
CREATE TABLE IF NOT EXISTS pacientes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    documento TEXT NOT NULL UNIQUE,
    nombre TEXT NOT NULL,
    apellido TEXT NOT NULL,
    edad INTEGER NOT NULL,
    sexo TEXT NOT NULL,
    fecha_nacimiento TEXT,
    telefono TEXT,
    peso REAL,
    altura REAL,
    activo INTEGER NOT NULL DEFAULT 1,
    fecha_creacion TEXT NOT NULL)
''')

columns_map = {
    'documento': 'document',
    'nombre': 'first_name',
    'apellido': 'last_name',
    'edad': 'age',
    'sexo': 'sex',
    'fecha_nacimiento': 'birth_date',
    'telefono': 'phone',
    'peso': 'peso',
    'altura': 'altura',
    'activo': 'active',
    'fecha_creacion': 'created_at'
}
transfer_data('patients', 'pacientes', columns_map)
print('  OK')

print('2. ESPECIALIDADES')
conn.execute('''
CREATE TABLE IF NOT EXISTS especialidades (
    id INTEGER PRIMARY KEY,
    nombre TEXT NOT NULL,
    precio REAL NOT NULL,
    duracion_minutos INTEGER NOT NULL,
    consultorio TEXT NOT NULL,
    nombre_medico TEXT NOT NULL)
''')
conn.execute('''
INSERT INTO especialidades (id, nombre, precio, duracion_minutos, consultorio, nombre_medico)
SELECT id, name, price, duration_min, room, doctor_name FROM specialties
''')
print('  OK')

print('3. CITAS')
conn.execute('''
CREATE TABLE IF NOT EXISTS citas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticket TEXT NOT NULL UNIQUE,
    id_paciente INTEGER NOT NULL,
    id_especialidad INTEGER NOT NULL,
    estado TEXT NOT NULL,
    estado_pago TEXT NOT NULL,
    estado_triaje TEXT NOT NULL,
    estado_consulta TEXT NOT NULL,
    estado_farmacia TEXT NOT NULL,
    consultorio TEXT,
    fecha_programada TEXT,
    codigo_recibo TEXT,
    fecha_creacion TEXT NOT NULL,
    fecha_pago TEXT)
''')
conn.execute('''
INSERT INTO citas (id, ticket, id_paciente, id_especialidad, estado, estado_pago, estado_triaje, estado_consulta, estado_farmacia, consultorio, fecha_programada, codigo_recibo, fecha_creacion, fecha_pago)
SELECT id, ticket, patient_id, specialty_id, status, payment_status, triage_status, consultation_status, pharmacy_status, room, scheduled_at, receipt_code, created_at, paid_at FROM appointments
''')
print('  OK')

print('4. EXPEDIENTES')
conn.execute('''
CREATE TABLE IF NOT EXISTS expedientes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    id_cita INTEGER NOT NULL UNIQUE,
    temperatura REAL NOT NULL,
    ritmo_cardiaco INTEGER NOT NULL,
    spo2 INTEGER NOT NULL,
    sistolica INTEGER NOT NULL,
    diastolica INTEGER NOT NULL,
    peso REAL NOT NULL,
    altura REAL NOT NULL,
    imc REAL NOT NULL,
    prioridad TEXT NOT NULL,
    puntuacion_riesgo REAL NOT NULL,
    etiqueta_riesgo TEXT NOT NULL,
    sistolica_predicha REAL NOT NULL,
    minutos_estimados REAL NOT NULL,
    resumen_decision TEXT NOT NULL,
    analisis_json TEXT NOT NULL,
    fuente TEXT NOT NULL,
    fecha_captura TEXT NOT NULL)
''')
conn.execute('''
INSERT INTO expedientes (id, id_cita, temperatura, ritmo_cardiaco, spo2, sistolica, diastolica, peso, altura, imc, prioridad, puntuacion_riesgo, etiqueta_riesgo, sistolica_predicha, minutos_estimados, resumen_decision, analisis_json, fuente, fecha_captura)
SELECT id, appointment_id, temperature, heart_rate, spo2, systolic, diastolic, weight, height, bmi, priority, risk_score, risk_label, predicted_systolic, estimated_attention_minutes, decision_summary, analysis_json, source, captured_at FROM triage_records
''')
print('  OK')

print('5. CONSULTAS')
conn.execute('''
CREATE TABLE IF NOT EXISTS consultas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    id_cita INTEGER NOT NULL UNIQUE,
    nombre_medico TEXT NOT NULL,
    sintomas TEXT NOT NULL,
    diagnostico TEXT NOT NULL,
    tratamiento TEXT NOT NULL,
    notas TEXT,
    fecha_creacion TEXT NOT NULL)
''')
conn.execute('''
INSERT INTO consultas (id, id_cita, nombre_medico, sintomas, diagnostico, tratamiento, notas, fecha_creacion)
SELECT id, appointment_id, doctor_name, symptoms, diagnosis, treatment_notes, notes, created_at FROM consultations
''')
print('  OK')

print('6. RECETAS')
conn.execute('''
CREATE TABLE IF NOT EXISTS recetas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    id_cita INTEGER NOT NULL,
    id_consulta INTEGER NOT NULL,
    estado TEXT NOT NULL,
    total REAL NOT NULL,
    fecha_creacion TEXT NOT NULL,
    fecha_dispensacion TEXT)
''')
conn.execute('''
INSERT INTO recetas (id, id_cita, id_consulta, estado, total, fecha_creacion, fecha_dispensacion)
SELECT id, appointment_id, consultation_id, status, total, created_at, dispensed_at FROM prescriptions
''')
print('  OK')

print('7. RECETA_ITEMS')
conn.execute('''
CREATE TABLE IF NOT EXISTS receta_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    id_receta INTEGER NOT NULL,
    medicina TEXT NOT NULL,
    dosis TEXT NOT NULL,
    frecuencia TEXT NOT NULL,
    dias INTEGER NOT NULL,
    cantidad INTEGER NOT NULL,
    precio_unitario REAL NOT NULL)
''')
conn.execute('''
INSERT INTO receta_items (id, id_receta, medicina, dosis, frecuencia, dias, cantidad, precio_unitario)
SELECT id, prescription_id, medicine, dosage, frequency, days, quantity, unit_price FROM prescription_items
''')
print('  OK')

print('8. TRABAJADORES')
conn.execute('''
CREATE TABLE IF NOT EXISTS trabajadores (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    documento TEXT NOT NULL UNIQUE,
    nombre TEXT NOT NULL,
    apellido TEXT NOT NULL,
    rol TEXT NOT NULL,
    especialidad TEXT,
    telefono TEXT,
    activo INTEGER NOT NULL DEFAULT 1,
    fecha_creacion TEXT NOT NULL,
    edad INTEGER,
    sexo TEXT,
    fecha_nacimiento TEXT)
''')
conn.execute('''
INSERT INTO trabajadores (documento, nombre, apellido, rol, especialidad, telefono, activo, fecha_creacion, edad, sexo, fecha_nacimiento)
SELECT document, first_name, last_name, role, specialty, phone, active, created_at, age, sex, birth_date FROM workers
''')
print('  OK')

print('9. CONSULTORIOS')
conn.execute('''
CREATE TABLE IF NOT EXISTS consultorios_new (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL,
    piso TEXT,
    equipo TEXT,
    activo INTEGER NOT NULL DEFAULT 1,
    fecha_creacion TEXT NOT NULL)
''')
conn.execute('''
INSERT INTO consultorios_new (nombre, piso, equipo, activo, fecha_creacion)
SELECT name, floor, equipment, active, created_at FROM consultorios
''')
print('  OK')

print('10. MEDICAMENTOS')
conn.execute('''
CREATE TABLE IF NOT EXISTS medicamentos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL,
    descripcion TEXT,
    precio REAL DEFAULT 0,
    stock INTEGER DEFAULT 0,
    activo INTEGER DEFAULT 1,
    fecha_creacion TEXT NOT NULL)
''')
conn.execute('''
INSERT INTO medicamentos (nombre, descripcion, precio, stock, activo, fecha_creacion)
SELECT name, description, price, stock, active, created_at FROM medications
''')
print('  OK')

print('11. TRANSACCIONES')
conn.execute('''
CREATE TABLE IF NOT EXISTS transacciones (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    codigo_transaccion TEXT NOT NULL UNIQUE,
    modulo TEXT NOT NULL,
    tipo_referencia TEXT NOT NULL,
    id_referencia INTEGER NOT NULL,
    documento_paciente TEXT,
    nombre_paciente TEXT,
    concepto TEXT NOT NULL,
    monto REAL NOT NULL,
    metodo_pago TEXT,
    estado TEXT NOT NULL,
    creado_por TEXT,
    fecha_creacion TEXT NOT NULL)
''')
conn.execute('''
INSERT INTO transacciones (codigo_transaccion, modulo, tipo_referencia, id_referencia, documento_paciente, nombre_paciente, concepto, monto, metodo_pago, estado, creado_por, fecha_creacion)
SELECT transaction_code, module, reference_type, reference_id, patient_document, patient_name, concept, amount, payment_method, status, created_by, created_at FROM transactions
''')
print('  OK')

print('12. CONFIGURACION')
conn.execute('''
CREATE TABLE IF NOT EXISTS configuracion (
    clave TEXT PRIMARY KEY,
    valor TEXT)
''')
conn.execute('''
INSERT INTO configuracion SELECT key, value FROM settings
''')
print('  OK')

print('13. EVENTOS_AUDITORIA')
conn.execute('''
CREATE TABLE IF NOT EXISTS eventos_auditoria (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tipo_evento TEXT NOT NULL,
    entidad TEXT,
    id_entidad INTEGER,
    mensaje TEXT,
    fecha_creacion TEXT NOT NULL)
''')
conn.execute('''
INSERT INTO eventos_auditoria (tipo_evento, entidad, id_entidad, mensaje, fecha_creacion)
SELECT event_type, entity, entity_id, message, created_at FROM audit_events
''')
print('  OK')

print('14. USUARIOS')
conn.execute('''
CREATE TABLE IF NOT EXISTS usuarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre_usuario TEXT NOT NULL,
    contrasena TEXT NOT NULL,
    nombre_completo TEXT NOT NULL,
    rol TEXT NOT NULL,
    activo INTEGER NOT NULL DEFAULT 1,
    fecha_creacion TEXT NOT NULL)
''')
conn.execute('''
INSERT INTO usuarios (nombre_usuario, contrasena, nombre_completo, rol, activo, fecha_creacion)
SELECT username, password, full_name, role, active, created_at FROM users
''')
print('  OK')

conn.commit()

# Fix consultorios table
conn.execute('DROP TABLE consultorios')
conn.execute('ALTER TABLE consultorios_new RENAME TO consultorios')
conn.commit()

# Drop old tables
print()
print('Eliminando tablas antiguas...')
old_tables = ['patients', 'specialties', 'appointments', 'triage_records', 'consultations', 'prescriptions', 'prescription_items', 'workers', 'medications', 'transactions', 'settings', 'audit_events', 'users']
for t in old_tables:
    try:
        conn.execute(f'DROP TABLE {t}')
    except:
        pass

conn.commit()
conn.close()
print('OK! Base de datos renombrada a espanol')
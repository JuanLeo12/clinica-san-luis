#!/usr/bin/env python3
"""Fix all views to use Spanish tables as source"""
import sqlite3

conn = sqlite3.connect('clinic_app.sqlite3')
c = conn.cursor()

# 1.appointments from citas
try:
    c.execute("DROP TABLE IF EXISTS appointments")
except:
    pass
sql_appts = """
CREATE VIEW appointments AS
SELECT
    id, ticket, id_paciente AS patient_id, id_especialidad AS specialty_id,
    estado AS status, estado_pago AS payment_status, estado_triaje AS triage_status,
    estado_consulta AS consultation_status, estado_farmacia AS pharmacy_status,
    consultorio AS room, fecha_programada AS scheduled_at, codigo_recibo AS receipt_code,
    fecha_creacion AS created_at, fecha_pago AS paid_at
FROM citas;
"""
c.execute(sql_appts)
print("appointments view created")

# 2.transactions from transacciones
try:
    c.execute("DROP TABLE IF EXISTS transactions")
except:
    pass
sql_trans = """
CREATE VIEW transactions AS
SELECT id, codigo_transaccion AS transaction_code, modulo AS module,
    tipo_referencia AS reference_type, id_reference AS appointment_id,
    documento_paciente AS patient_document, nombre_paciente AS patient_name,
    concepto AS concept, monto AS amount, metodo_pago AS payment_method,
    estado AS status, creado_por AS created_by, fecha_creacion AS created_at
FROM transacciones;
"""
c.execute(sql_trans)
print("transactions view created")

# 3.prescriptions from recetas
try:
    c.execute("DROP TABLE IF EXISTS prescriptions")
except:
    pass
sql_rx = """
CREATE VIEW prescriptions AS
SELECT id, id_cita AS appointment_id, id_consulta AS consultation_id,
    estado AS status, total AS total, fecha_creacion AS created_at,
    fecha_dispensacion AS dispensed_at
FROM recetas;
"""
c.execute(sql_rx)
print("prescriptions view created")

# 4.consultations from consultas
try:
    c.execute("DROP TABLE IF EXISTS consultations")
except:
    pass
sql_cons = """
CREATE VIEW consultations AS
SELECT id, id_cita AS appointment_id, nombre_medico AS doctor_name,
    sintomas AS symptoms, diagnostico AS diagnosis, tratamiento AS treatment,
    notas AS notes, fecha_creacion AS created_at
FROM consultas;
"""
c.execute(sql_cons)
print("consultations view created")

# 5.triage_records from expedientes
try:
    c.execute("DROP TABLE IF EXISTS triage_records")
except:
    pass
sql_triage = """
CREATE VIEW triage_records AS
SELECT id, id_cita AS appointment_id, temperatura AS temperature,
    ritmo_cardiaco AS heart_rate, spo2, sistolica AS systolic,
    diastolica AS diastolic, peso AS weight, altura AS height, imc AS bmi,
    prioridad AS priority, puntuacion_riesgo AS risk_score,
    etiqueta_riesgo AS risk_label, sistolica_predicha AS predicted_systolic,
    minutos_estimados AS estimated_attention_minutes, resumen_decision AS decision_summary,
    analisis_json AS analysis_json, fuente AS source, fecha_captura AS captured_at
FROM expedientes;
"""
c.execute(sql_triage)
print("triage_records view created")

# Now create INSTEAD OF triggers for inserts/updates/deletes
triggers = [
("appointments_insert", "appointments", "appointments", "citas"),
("transactions_insert", "transactions", "transactions", "transacciones"),
("prescriptions_insert", "prescriptions", "prescriptions", "recetas"),
("consultations_insert", "consultations", "consultations", "consultas"),
("triage_records_insert", "triage_records", "triage_records", "expedientes")
]

for trigger_name, view_name, new_name, table_name in triggers:
    sql = f"""
    CREATE TRIGGER IF NOT EXISTS {trigger_name} INSTEAD OF INSERT ON {view_name} FOR EACH ROW
    BEGIN
        INSERT INTO {table_name} (id_paciente, id_especialidad, estado, estado_pago, estado_triaje, estado_consulta, estado_farmacia, consultorio, fecha_programada, codigo_recibo, fecha_creacion)
        VALUES (NEW.patient_id, NEW.specialty_id, NEW.status, NEW.payment_status, NEW.triage_status, NEW.consultation_status, NEW.pharmacy_status, NEW.room, NEW.scheduled_at, NEW.receipt_code, NEW.created_at);
    END;
    """
    try:
        c.execute(sql)
    except:
        pass

conn.commit()

# Verify counts
for name in ['appointments', 'transactions', 'prescriptions', 'consultations', 'triage_records']:
    c.execute(f'SELECT COUNT(*) FROM {name}')
    print(f'{name}: {c.fetchone()[0]}')

conn.close()
print("Done!")
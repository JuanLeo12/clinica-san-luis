#!/usr/bin/env python3
"""Script to create database views mapping English table names to Spanish tables."""
import sqlite3
import sys

def main():
    conn = sqlite3.connect('clinic_app.sqlite3')
    cursor = conn.cursor()

    # Create views
    views = [
        ("patients", """
        CREATE VIEW IF NOT EXISTS patients AS
        SELECT id, documento AS document, nombre AS first_name, apellido AS last_name,
               edad AS age, sexo AS sex, fecha_nacimiento AS birth_date,
               telefono AS phone, peso, altura, activo, created_at
        FROM pacientes
        """),
        ("specialties", """
        CREATE VIEW IF NOT EXISTS specialties AS
        SELECT id, nombre AS name, precio AS price, duracion_minutos AS duration_min,
               consultorio AS room, nombre_medico AS doctor_name
        FROM especialidades
        """),
        ("appointments", """
        CREATE VIEW IF NOT EXISTS appointments AS
        SELECT id, ticket, id_paciente AS patient_id, id_especialidad AS specialty_id,
               estado AS status, estado_pago AS payment_status, estado_triaje AS triage_status,
               estado_consulta AS consultation_status, estado_farmacia AS pharmacy_status,
               consultorio AS room, fecha_programada AS scheduled_at, codigo_recibo AS receipt_code,
               fecha_creacion AS created_at, fecha_pago AS paid_at
        FROM citas
        """),
        ("transactions", """
        CREATE VIEW IF NOT EXISTS transactions AS
        SELECT id, codigo_transaccion AS transaction_code, modulo AS module,
               tipo_referencia AS reference_type, id_reference AS appointment_id,
               documento_paciente AS patient_document, nombre_paciente AS patient_name,
               concepto AS concept, monto AS amount, metodo_pago AS payment_method,
               estado AS status, creado_por AS created_by, fecha_creacion AS created_at
        FROM transacciones
        """),
        ("workers", """
        CREATE VIEW IF NOT EXISTS workers AS
        SELECT id, documento AS document, nombre AS first_name, apellido AS last_name,
               rol AS role, especialidad AS specialty, telefono AS phone,
               activo, created_at, edad AS age, sexo AS sex, fecha_nacimiento AS birth_date
        FROM trabajadores
        """),
        ("consultorios", """
        CREATE VIEW IF NOT EXISTS consultorios AS
        SELECT id, nombre AS name, piso AS floor, equipo AS equipment, activo, created_at
        FROM consultorios
        """),
        ("medications", """
        CREATE VIEW IF NOT EXISTS medications AS
        SELECT id, nombre AS name, descripcion AS description,
               precio AS price, stock, unidad
        FROM medicamentos
        """),
        ("triage_records", """
        CREATE VIEW IF NOT EXISTS triage_records AS
        SELECT id, id_cita AS appointment_id, temperatura AS temperature,
               ritmo_cardiaco AS heart_rate, spo2, sistolica AS systolic,
               diastolica AS diastolic, peso AS weight, altura AS height, imc AS bmi,
               prioridad AS priority, puntuacion_riesgo AS risk_score,
               etiqueta_riesgo AS risk_label, sistolica_predicha AS predicted_systolic,
               minutos_estimados AS estimated_attention_minutes, resumen_decision AS decision_summary,
               analisis_json AS analysis_json, fuente AS source, fecha_captura AS captured_at
        FROM expedientes
        """),
        ("consultations", """
        CREATE VIEW IF NOT EXISTS consultations AS
        SELECT id, id_cita AS appointment_id, nombre_medico AS doctor_name,
               sintomas AS symptoms, diagnostico AS diagnosis, tratamiento AS treatment,
               notas AS notes, fecha_creacion AS created_at
        FROM consultas
        """),
        ("prescriptions", """
        CREATE VIEW IF NOT EXISTS prescriptions AS
        SELECT id, id_cita AS appointment_id, id_consulta AS consultation_id,
               estado AS status, total AS total, fecha_creacion AS created_at,
               fecha_dispensacion AS dispensed_at
        FROM recetas
        """),
        ("prescription_items", """
        CREATE VIEW IF NOT EXISTS prescription_items AS
        SELECT id, id_receta AS prescription_id, medicina AS medication,
               dosis, frecuencia AS frequency, dias AS days, cantidad AS quantity,
               precio_unitario AS unit_price
        FROM receta_items
        """),
    ]

    for view_name, sql in views:
        try:
            conn.executescript(sql)
            print(f"Created view: {view_name}")
        except Exception as e:
            print(f"Error creating view {view_name}: {e}")

    # Fix settings table - add key column as copy of name
    try:
        cursor.execute("PRAGMA table_info(settings)")
        columns = [col[1] for col in cursor.fetchall()]
        if 'key' not in columns:
            cursor.execute("ALTER TABLE settings ADD COLUMN key TEXT")
            cursor.execute("UPDATE settings SET key = name")
            conn.commit()
            print("Added key column to settings table")
        else:
            print("Settings already has key column")
    except Exception as e:
        print(f"Error fixing settings table: {e}")

    conn.close()
    print("Done!")

if __name__ == '__main__':
    main()
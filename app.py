from __future__ import annotations

import json
import os
from datetime import date, datetime
from pathlib import Path
from typing import Any, Dict

import requests
from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request

from clinic_ai import ClinicalML
from storage import create_repository

load_dotenv()

DEFAULT_IOT_DATA = {
    "temperature": 36.5,
    "heart_rate": 75,
    "spO2": 98,
    "blood_pressure_systolic": 120,
    "blood_pressure_diastolic": 80,
    "weight": 70.0,
    "height": 170.0,
}

latest_iot_data: Dict[str, Any] = DEFAULT_IOT_DATA.copy()
ml_engine = ClinicalML()
CONSULTADNI_TOKEN = os.getenv("CONSULTADNI_TOKEN", "")


def _transform_patient(p):
    """Transform Spanish patient fields to English for frontend"""
    first_name = p.get("nombre", "")
    last_name = p.get("apellido", "")
    return {
        "id": p.get("id"),
        "document": p.get("documento"),
        "first_name": first_name,
        "last_name": last_name,
        "full_name": f"{first_name} {last_name}".strip(),
        "age": p.get("edad"),
        "sex": p.get("sexo"),
        "phone": p.get("telefono"),
        "birth_date": p.get("fecha_nacimiento"),
        "peso": p.get("peso"),
        "altura": p.get("altura"),
        "active": p.get("activo"),
    }


def _translate_status(status: str, status_type: str) -> str:
    """Translate status values from database to what frontend expects"""
    # Spanish to English translations
    es_to_en = {
        "pendiente": "pending",
        "pagado": "paid",
        "no_iniciado": "not_started",
        "esperando": "waiting",
        "finalizado": "completed",
        "no_entregado": "not_started",
        "entregado": "completed",
        "ninguno": "none",
        "dispensado": "dispensed",
    }
    # Database demo values to frontend expected values
    db_to_frontend = {
        "registered": "pending",
        "triedadd": "in_progress",
        "done": "completed",
        "none": "not_started",
    }
    # Prescription status values (both Spanish and English)
    prescription_map = {
        "pendiente": "pending",
        "dispensado": "dispensed",
        "prescription_pending": "pending",
        "dispensed": "dispensed",
        "pending": "pending",
        "completed": "completed",
    }

    # Handle prescription status specifically
    if status_type == "prescription":
        return prescription_map.get(status, status)

    # First try Spanish to English
    if status in es_to_en:
        return es_to_en[status]
    # Then try database demo to frontend expected
    if status in db_to_frontend:
        return db_to_frontend[status]
    return status


def _transform_workers(workers):
    """Transform Spanish worker fields to English"""
    return [{
        "id": w.get("id"),
        "document": w.get("documento"),
        "first_name": w.get("nombre"),
        "last_name": w.get("apellido"),
        "role": w.get("rol"),
        "specialty": w.get("especialidad"),
        "phone": w.get("telefono"),
        "active": w.get("activo"),
    } for w in workers]


def create_app() -> Flask:
    app = Flask(__name__, static_folder="public/static", static_url_path="/static")
    repo = create_repository()
    repo.setup()
    app.config["repo"] = repo

    @app.after_request
    def add_cors_headers(response):
        response.headers["Access-Control-Allow-Origin"] = os.getenv("CORS_ORIGIN", "*")
        response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, PATCH, DELETE, OPTIONS"
        return response

    @app.route("/")
    @app.route("/display")
    def index():
        return render_template("index.html")

    @app.route("/login")
    def render_login():
        return render_template("login.html")

    @app.route("/triage_dataset.csv")
    def serve_dataset_csv():
        import os
        csv_path = os.path.join(os.path.dirname(__file__), "triage_dataset.csv")
        from flask import send_file
        return send_file(csv_path, mimetype="text/csv")

    @app.route("/api/ping", methods=["GET"])
    def ping():
        return jsonify({"status": "ok"}), 200

    @app.route("/api/state", methods=["GET"])
    def state():
        repo = app.config["repo"]
        snapshot = repo.snapshot()
        snapshot["latest_iot"] = latest_iot_data
        snapshot["storage"] = os.getenv("APP_STORAGE", "sqlite")
        snapshot["active_triage_appointment_id"] = repo.get_setting("activo_triedad_id_cita")
        # Transform Spanish fields to English for frontend
        patients = [_transform_patient(p) for p in snapshot.get("pacientes", [])]
        workers = _transform_workers(snapshot.get("trabajadores", []))
        # Create lookups for adding to appointments
        patient_map = {p["id"]: p for p in patients}
        # Transform specialties too
        specialties = snapshot.get("especialidades", [])
        specialty_map = {s["id"]: s for s in specialties}
        # Get triaje/expediente data
        expediente_data = snapshot.get("expedientes", [])
        expediente_map = {e.get("id_cita"): e for e in expediente_data}
        # Get consultation data
        consulta_data = snapshot.get("consultas", [])
        consulta_map = {c.get("id_cita"): c for c in consulta_data}
        snapshot["patients"] = patients
        snapshot["workers"] = workers
        # Add derived fields to appointments (patient, specialty, etc.)
        appointments = []
        for apt in snapshot.get("citas", []):
            # Add patient object
            patient = patient_map.get(apt.get("id_paciente"))
            if patient:
                apt["patient"] = {
                    "id": patient["id"],
                    "document": patient["document"],
                    "full_name": f"{patient['first_name']} {patient['last_name']}",
                    "first_name": patient["first_name"],
                    "last_name": patient["last_name"],
                    "age": patient["age"],
                    "sex": patient["sex"],
                    "phone": patient["phone"],
                }
            # Add specialty object
            specialty = specialty_map.get(apt.get("id_especialidad"))
            if specialty:
                apt["specialty"] = {
                    "id": specialty["id"],
                    "name": specialty.get("nombre", ""),
                    "price": specialty.get("precio", 0),
                    "duration_minutes": specialty.get("duracion_minutos", 30),
                }
            # Add English aliases for status fields (frontend expects these)
            apt["status"] = _translate_status(apt.get("estado", ""), "general")
            apt["payment_status"] = _translate_status(apt.get("estado_pago", ""), "payment")
            apt["triage_status"] = _translate_status(apt.get("estado_triaje", ""), "triage")
            apt["consultation_status"] = _translate_status(apt.get("estado_consulta", ""), "consultation")
            apt["pharmacy_status"] = _translate_status(apt.get("estado_farmacia", ""), "pharmacy")
            apt["room"] = apt.get("consultorio", "")
            # Add creation date for timeline display
            apt["created_at"] = apt.get("fecha_creacion", "")
            # Add triaje data (expediente) if available
            exp = expediente_map.get(apt.get("id"))
            if exp:
                peso = exp.get("peso", 0)
                altura = exp.get("altura", 0)
                # Calcular IMC (BMI en inglés) = peso(kg) / altura(m)^2
                imc = 0
                if peso and altura and altura > 0:
                    imc = round(peso / ((altura / 100) ** 2), 1)
                # Parse analysis JSON if available
                analysis = {}
                try:
                    analisis_json = exp.get("analisis_json", "")
                    if analisis_json:
                        import json
                        analysis = json.loads(analisis_json) if isinstance(analisis_json, str) else analisis_json
                except Exception:
                    pass
                apt["triage"] = {
                    "priority": exp.get("prioridad", "Rutina"),
                    "risk_score": exp.get("puntuacion_riesgo", 0),
                    "risk_label": exp.get("etiqueta_riesgo", "Bajo"),
                    "estimated_attention_minutes": exp.get("minutos_estimados", 15),
                    "heart_rate": exp.get("ritmo_cardiaco"),
                    "spo2": exp.get("spo2"),
                    "systolic": exp.get("sistolica"),
                    "diastolic": exp.get("diastolica"),
                    "temperature": exp.get("temperatura"),
                    "weight": peso,
                    "height": altura,
                    "bmi": imc,
                    "predicted_systolic": exp.get("sistolica_predicha"),
                    "decision_summary": exp.get("resumen_decision", ""),
                    "analysis": analysis,
                }
            # Add consultation data if available
            cons = consulta_map.get(apt.get("id"))
            if cons:
                apt["consultation"] = {
                    "symptoms": cons.get("sintomas", ""),
                    "diagnosis": cons.get("diagnostico", ""),
                    "treatment": cons.get("tratamiento", ""),
                    "notes": cons.get("notas", ""),
                    "doctor_name": cons.get("nombre_medico", ""),
                }
            appointments.append(apt)
        # Keep Spanish keys too for reference
        snapshot["specialties"] = specialties
        # Add English aliases for specialties
        for s in specialties:
            s["name"] = s.get("nombre", "")
            s["price"] = s.get("precio", 0)
            s["room"] = s.get("consultorio", "")
            s["duration_minutes"] = s.get("duracion_minutos", 30)
        snapshot["appointments"] = appointments
        # Add English aliases for consultations
        consultas = snapshot.get("consultas", [])
        for c in consultas:
            c["symptoms"] = c.get("sintomas", "")
            c["diagnosis"] = c.get("diagnostico", "")
            c["treatment"] = c.get("tratamiento", "")
            c["notes"] = c.get("notas", "")
            c["doctor_name"] = c.get("nombre_medico", "")
        snapshot["consultations"] = consultas
        # Add English aliases for prescriptions
        recetas = snapshot.get("recetas", [])
        # Create lookup for appointments
        cita_map = {c.get("id"): c for c in snapshot.get("citas", [])}
        # Create lookup for consultations (diagnosis)
        consulta_map = {c.get("id_cita"): c for c in snapshot.get("consultas", [])}
        for r in recetas:
            # Ensure id is preserved
            r["id"] = r.get("id")
            # Translate status values: prescription_pending -> pending, dispensed -> dispensed
            raw_status = r.get("estado", "")
            r["status"] = _translate_status(raw_status, "prescription")
            r["total"] = r.get("total", 0)
            # Link to patient and appointment data
            id_cita = r.get("id_cita")
            cita = cita_map.get(id_cita)
            if cita:
                # Get ticket from appointment
                r["ticket"] = cita.get("ticket", "")
                r["appointment_id"] = id_cita
                # Get patient data
                id_paciente = cita.get("id_paciente")
                paciente = next((p for p in snapshot.get("pacientes", []) if p.get("id") == id_paciente), None)
                if paciente:
                    r["patient_name"] = f"{paciente.get('nombre', '')} {paciente.get('apellido', '')}".strip()
                    r["patient_document"] = paciente.get("documento", "")
                # Get diagnosis from consultation
                consulta = consulta_map.get(id_cita)
                if consulta:
                    r["diagnosis"] = consulta.get("diagnostico", "")
            else:
                r["ticket"] = ""
                r["appointment_id"] = id_cita
                r["diagnosis"] = ""
            # Add items to prescription
            items = [dict(i) for i in snapshot.get("receta_items", []) if i.get("id_receta") == r.get("id")]
            for item in items:
                item["medicine"] = item.get("medicina", "") or item.get("medicamento", "")
                item["dosage"] = item.get("dosis", "")
                item["frequency"] = item.get("frecuencia", "")
                item["days"] = item.get("dias", 0)
                item["quantity"] = item.get("cantidad", 0)
                item["unit_price"] = item.get("precio_unitario", 0) or item.get("unit_precio", 0)
            r["items"] = items
        snapshot["prescriptions"] = recetas
        # Add English aliases for transactions
        transacciones = snapshot.get("transacciones", [])
        for t in transacciones:
            t["transaction_code"] = t.get("codigo_transaccion", "")
            t["concept"] = t.get("concepto", "")
            t["created_by"] = t.get("creado_por", "")
            t["patient_document"] = t.get("documento_paciente", "")
            # Link to patient name
            doc_paciente = t.get("documento_paciente")
            if doc_paciente:
                paciente = next((p for p in snapshot.get("pacientes", []) if p.get("documento") == doc_paciente), None)
                if paciente:
                    t["patient_name"] = f"{paciente.get('nombre', '')} {paciente.get('apellido', '')}".strip()
            t["status"] = _translate_status(t.get("estado", ""), "payment")
            t["payment_method"] = t.get("metodo_pago", "")
            t["module"] = t.get("modulo", "")
            t["amount"] = t.get("monto", 0)
            t["created_at"] = t.get("fecha_creacion", "")
        snapshot["transactions"] = transacciones
        # Add English aliases for rooms and medications
        consultorios = snapshot.get("consultorios", [])
        for r in consultorios:
            r["name"] = r.get("nombre", "")
            r["active"] = r.get("activo", 1)
        snapshot["rooms"] = consultorios
        medicamentos = snapshot.get("medicamentos", [])
        for m in medicamentos:
            m["name"] = m.get("nombre", "")
            m["medicine"] = m.get("nombre", "")
            m["price"] = m.get("precio", 0)
            m["unit_price"] = m.get("precio", 0)
            m["stock"] = m.get("stock", 0)
            m["description"] = m.get("descripcion", "")
            m["active"] = m.get("activo", 1)
        snapshot["medications"] = medicamentos
        return jsonify(snapshot), 200

    @app.route("/api/specialties", methods=["GET"])
    def specialties():
        raw = repo.list_specialties()
        transformed = []
        for s in raw:
            transformed.append({
                "id": s.get("id"),
                "name": s.get("nombre", ""),
                "price": s.get("precio", 0),
                "room": s.get("consultorio", ""),
                "duration_minutes": s.get("duracion_minutos", 30),
            })
        return jsonify({"specialties": transformed}), 200

    @app.route("/api/appointments", methods=["POST"])
    def create_appointment():
        payload = _json_payload()
        appointment = repo.create_patient_and_appointment(payload)
        return jsonify({"appointment": appointment}), 201

    @app.route("/api/appointments/<int:appointment_id>/pay", methods=["POST"])
    def pay_appointment(appointment_id: int):
        payload = _json_payload(required=False)
        appointment = repo.mark_paid(
            appointment_id,
            metodo_pago=str(payload.get("payment_method") or "Efectivo"),
            creado_por=str(payload.get("created_by") or ""),
        )
        # Crear transacción después del pago
        if appointment.get("estado_pago") == "paid":
            patient = appointment.get("patient", {})
            specialty = appointment.get("specialty", {})
            repo.create_transaction(
                modulo="cashier",
                tipo_referencia="appointment",
                id_referencia=appointment_id,
                documento_paciente=patient.get("documento", ""),
                nombre_paciente=f"{patient.get('nombre', '')} {patient.get('apellido', '')}".strip(),
                concepto=f"Consulta - {specialty.get('nombre', 'Especialidad')}",
                monto=specialty.get("price", 0),
                metodo_pago=str(payload.get("payment_method") or "Efectivo"),
                creado_por=str(payload.get("created_by") or ""),
            )
        return jsonify({"appointment": appointment}), 200

    @app.route("/api/triage/<int:appointment_id>/activate", methods=["POST"])
    def activate_triage(appointment_id: int):
        appointment = repo.set_active_triage(appointment_id)
        return jsonify({"appointment": appointment}), 200

    @app.route("/api/triage/<int:appointment_id>/capture", methods=["POST"])
    def capture_triage(appointment_id: int):
        payload = _json_payload()
        appointment = repo.get_appointment(appointment_id)
        if appointment is None:
            return jsonify({"status": "error", "message": "Cita no encontrada."}), 404

        vitals = _normalize_vitals(payload.get("vitals") or payload or latest_iot_data)
        analysis = ml_engine.analyze(vitals, appointment.get("patient"))
        source = str(payload.get("source") or "IoT").strip() or "IoT"
        appointment = repo.capture_triage(appointment_id, vitals, analysis, source)
        return jsonify({"appointment": appointment, "analysis": analysis}), 200

    @app.route("/api/consultations/<int:appointment_id>", methods=["POST"])
    def save_consultation(appointment_id: int):
        payload = _json_payload()
        appointment = repo.create_consultation(appointment_id, payload)
        return jsonify({"appointment": appointment}), 200

    @app.route("/api/prescriptions/<int:prescription_id>/dispense", methods=["POST"])
    def dispense_prescription(prescription_id: int):
        payload = _json_payload(required=False)
        prescription = repo.dispense_prescription(
            prescription_id,
            payment_method=str(payload.get("payment_method") or "Efectivo"),
            created_by=str(payload.get("created_by") or ""),
        )
        # Crear transacción después de dispensar
        if prescription.get("estado") == "dispensed":
            patient = prescription.get("patient", {})
            repo.create_transaction(
                modulo="pharmacy",
                tipo_referencia="prescription",
                id_referencia=prescription_id,
                documento_paciente=prescription.get("documento_paciente", ""),
                nombre_paciente=prescription.get("nombre_paciente", ""),
                concepto="Medicamentos - Receta",
                monto=prescription.get("total", 0),
                metodo_pago=str(payload.get("payment_method") or "Efectivo"),
                creado_por=str(payload.get("created_by") or ""),
            )
        return jsonify({"prescription": prescription}), 200

    @app.route("/api/auth/login", methods=["POST"])
    def login():
        payload = _json_payload()
        username = payload.get("username") or ""
        password = payload.get("password") or ""
        user = repo.authenticate_user(username, password)
        if user is None:
            return jsonify({"status": "error", "message": "Credenciales invalidas"}), 401

        # Mapear nombres de campos de español a inglés
        user_en = {
            "username": user.get("nombre_usuario"),
            "full_name": user.get("nombre_completo"),
            "role": user.get("rol"),
            "id": user.get("id"),
            "active": user.get("activo"),
        }

        # Redirigir según el rol
        role_first_view = {
            "admin": "admin",
            "reception": "reception",
            "cashier": "cashier",
            "triage": "triage",
            "doctor": "doctor",
            "pharmacy": "pharmacy"
        }
        first_view = role_first_view.get(user_en.get("role"), "dashboard")
        return jsonify({"user": user_en, "redirect": "/#" + first_view}), 200


    @app.route("/api/auth/logout", methods=["POST"])
    def logout():
        return jsonify({"status": "ok"}), 200

    @app.route("/api/ml/analyze", methods=["POST"])
    def analyze_vitals():
        payload = _json_payload()
        vitals = _normalize_vitals(payload.get("vitals") or payload)
        patient = payload.get("patient") or {}
        return jsonify({"analysis": ml_engine.analyze(vitals, patient)}), 200

    @app.route("/api/ml/explain", methods=["GET"])
    def explain_ml():
        return jsonify(ml_engine.model_info()), 200

    @app.route("/api/ml/evaluate", methods=["GET"])
    def evaluate_ml():
        repo = app.config["repo"]
        return jsonify(ml_engine.dashboard_metrics(repo.snapshot().get("appointments", []))), 200

    @app.route("/api/ml/dashboard", methods=["GET"])
    def ml_dashboard():
        return jsonify(ml_engine.dashboard_metrics(repo.snapshot().get("appointments", []))), 200

    @app.route("/api/dni/<dni>", methods=["GET"])
    def lookup_dni(dni: str):
        clean_dni = "".join(char for char in str(dni) if char.isdigit())
        if len(clean_dni) != 8:
            return jsonify({"status": "error", "message": "El DNI debe tener 8 digitos."}), 400
        if not CONSULTADNI_TOKEN:
            return (
                jsonify({"status": "error", "message": "Configure CONSULTADNI_TOKEN para buscar DNI."}),
                503,
            )

        try:
            response = requests.get(
                "https://www.consultadni.com/api/v1/dni/completo",
                params={"document": clean_dni, "key": CONSULTADNI_TOKEN},
                headers={"Accept": "application/json"},
                timeout=12,
            )
            if response.status_code >= 400:
                return (
                    jsonify({"status": "error", "message": "No se encontro informacion para el DNI."}),
                    404,
                )
            payload = response.json()
        except requests.RequestException:
            return jsonify({"status": "error", "message": "No se pudo conectar con la busqueda por DNI."}), 502

        data = _dni_data_node(payload)
        first_name = _lookup_value(
            data,
            "nombres",
            "nombres_completos",
            "nombre",
            "name",
            "names",
            "prenombres",
        )
        paternal = _lookup_value(
            data,
            "apellido_paterno",
            "apellidoPaterno",
            "ap_paterno",
            "apPaterno",
            "paterno",
            "ape_paterno",
        )
        maternal = _lookup_value(
            data,
            "apellido_materno",
            "apellidoMaterno",
            "ap_materno",
            "apMaterno",
            "materno",
            "ape_materno",
        )
        last_name = (
            " ".join(part for part in [paternal, maternal] if part).strip()
            or _lookup_value(data, "apellidos", "apellido", "last_name", "lastName")
        )
        full_name = _lookup_value(
            data,
            "nombre_completo",
            "nombreCompleto",
            "full_name",
            "fullName",
            "razon_social",
        )
        if full_name and (not first_name or not last_name):
            guessed_first_name, guessed_last_name = _split_full_name(full_name)
            first_name = first_name or guessed_first_name
            last_name = last_name or guessed_last_name
        birth_date = _extract_birth_date(data)
        sex = _normalize_sex(_lookup_value(data, "sexo", "genero", "gender", "sex"))
        if not first_name or not last_name:
            return jsonify(
                {
                    "status": "error",
                    "message": "La API respondio, pero no devolvio nombres y apellidos reconocibles.",
                }
            ), 422
        person = {
            "document": clean_dni,
            "first_name": first_name,
            "paternal_last_name": paternal,
            "maternal_last_name": maternal,
            "last_name": last_name,
            "age": _calculate_age(birth_date) if birth_date else None,
            "birth_date": birth_date.isoformat() if birth_date else "",
            "sex": sex,
        }
        return jsonify(
            {
                "status": "ok",
                "person": person,
                "patient": person,
            }
        ), 200

    @app.route("/api/data", methods=["GET", "POST"])
    def data_endpoint():
        global latest_iot_data
        if request.method == "POST":
            payload = _json_payload(required=False)
            if not payload:
                return jsonify({"status": "error", "message": "No se recibio JSON valido"}), 400
            latest_iot_data = _normalize_vitals({**latest_iot_data, **payload})
            return (
                jsonify(
                    {
                        "status": "success",
                        "message": "Datos IoT actualizados",
                        "data": latest_iot_data,
                        "active_triage_appointment_id": repo.get_setting(
                            "activo_triedad_id_cita"
                        ),
                    }
                ),
                200,
            )
        return jsonify(latest_iot_data), 200

    @app.route("/update")
    def get_main_py():
        main_path = Path(__file__).with_name("main.py")
        return main_path.read_text(encoding="utf-8"), 200, {
            "Content-Type": "text/plain; charset=utf-8"
        }

    @app.route("/api/appointments/<int:appointment_id>/call", methods=["POST"])
    def call_patient(appointment_id: int):
        payload = _json_payload(required=False)
        target = str(payload.get("target") or "doctor").strip()
        setting = "called_triage_appointment_id" if target == "triage" else "called_doctor_appointment_id"
        repo.set_setting(setting, str(appointment_id))
        return jsonify({"status": "ok", "appointment_id": appointment_id, "target": target}), 200

    @app.route("/api/appointments/<int:appointment_id>/complete_call", methods=["POST"])
    def complete_call(appointment_id: int):
        payload = _json_payload(required=False)
        target = str(payload.get("target") or "doctor").strip()
        setting = "called_triage_appointment_id" if target == "triage" else "called_doctor_appointment_id"
        repo.set_setting(setting, None)
        return jsonify({"status": "ok"}), 200

    @app.route("/api/called", methods=["GET"])
    def get_called():
        triage_id = repo.get_setting("called_triage_appointment_id")
        doctor_id = repo.get_setting("called_doctor_appointment_id")
        return jsonify(
            {
                "triage": repo.get_appointment(int(triage_id)) if triage_id else None,
                "doctor": repo.get_appointment(int(doctor_id)) if doctor_id else None,
            }
        ), 200
    
        # Workers API
    @app.route("/api/workers", methods=["GET"])
    def list_workers():
        repo = app.config["repo"]
        workers = repo.list_workers()
        return jsonify({"workers": _transform_workers(workers)}), 200

    @app.route("/api/workers", methods=["POST"])
    def create_worker():
        worker = repo.create_worker(_json_payload())
        return jsonify({"worker": worker}), 201

    @app.route("/api/workers/<int:worker_id>", methods=["PUT"])
    def update_worker(worker_id):
        worker = repo.update_worker(worker_id, _json_payload())
        return jsonify({"worker": worker}), 200

    @app.route("/api/workers/<int:worker_id>", methods=["DELETE"])
    def delete_worker(worker_id):
        repo.delete_worker(worker_id)
        return jsonify({"status": "ok"}), 200

    # Consultorios API
    @app.route("/api/consultorios", methods=["GET"])
    def list_consultorios():
        rooms = repo.list_consultorios()
        # Add English aliases
        for r in rooms:
            r["name"] = r.get("nombre", "")
            r["active"] = r.get("activo", 1)
        return jsonify({"consultorios": rooms}), 200

    @app.route("/api/consultorios", methods=["POST"])
    def create_consultorio():
        c = repo.create_consultorio(_json_payload())
        return jsonify({"consultorio": c}), 201

    @app.route("/api/consultorios/<int:consultorio_id>", methods=["PUT"])
    def update_consultorio(consultorio_id):
        c = repo.update_consultorio(consultorio_id, _json_payload())
        return jsonify({"consultorio": c}), 200

    @app.route("/api/consultorios/<int:consultorio_id>", methods=["DELETE"])
    def delete_consultorio(consultorio_id):
        repo.delete_consultorio(consultorio_id)
        return jsonify({"status": "ok"}), 200

    # Medications API
    @app.route("/api/medications", methods=["GET"])
    def list_medications():
        meds = repo.list_medications()
        # Add English aliases
        for m in meds:
            m["medicine"] = m.get("nombre", "")
            m["unit_price"] = m.get("precio", 0)
            m["description"] = m.get("descripcion", "")
            m["active"] = m.get("activo", 1)
        return jsonify({"medications": meds}), 200

    @app.route("/api/medications", methods=["POST"])
    def create_medication():
        m = repo.create_medication(_json_payload())
        return jsonify({"medication": m}), 201

    @app.route("/api/medications/<int:medication_id>", methods=["PUT"])
    def update_medication(medication_id):
        m = repo.update_medication(medication_id, _json_payload())
        return jsonify({"medication": m}), 200

    @app.route("/api/medications/<int:medication_id>", methods=["DELETE"])
    def delete_medication(medication_id):
        repo.delete_medication(medication_id)
        return jsonify({"status": "ok"}), 200

    # Search Patients API
    @app.route("/api/patients/search", methods=["GET"])
    def search_patients():
        query = request.args.get("q", "")
        repo = app.config["repo"]
        patients = repo.search_patients(query)
        return jsonify({"patients": [_transform_patient(p) for p in patients]}), 200

    # Patients API
    @app.route("/api/patients", methods=["GET"])
    def list_patients():
        repo = app.config["repo"]
        patients = repo.list_patients()
        return jsonify({"patients": [_transform_patient(p) for p in patients]}), 200

    @app.route("/api/patients", methods=["POST"])
    def create_patient():
        patient = repo.create_patient(_json_payload())
        return jsonify({"patient": patient}), 201

    @app.route("/api/patients/<int:patient_id>", methods=["PUT"])
    def update_patient(patient_id):
        patient = repo.update_patient(patient_id, _json_payload())
        return jsonify({"patient": patient}), 200

    @app.route("/api/patients/<int:patient_id>", methods=["DELETE"])
    def delete_patient(patient_id):
        repo.delete_patient(patient_id)
        return jsonify({"status": "ok"}), 200




    @app.errorhandler(ValueError)
    def handle_value_error(error: ValueError):
        import traceback
        return jsonify({"status": "error", "message": str(error), "trace": traceback.format_exc()}), 400

    @app.errorhandler(RuntimeError)
    def handle_runtime_error(error: RuntimeError):
        import traceback
        return jsonify({"status": "error", "message": str(error), "trace": traceback.format_exc()}), 500

    @app.errorhandler(RecursionError)
    def handle_recursion_error(error: RecursionError):
        import traceback
        return jsonify({"status": "error", "message": str(error), "trace": traceback.format_exc()}), 500

    return app


def _json_payload(required: bool = True) -> Dict[str, Any]:
    payload = request.get_json(silent=True)
    if payload is None:
        raw = request.get_data(as_text=True)
        if raw:
            try:
                payload = json.loads(raw)
            except json.JSONDecodeError:
                payload = None
    if payload is None:
        if required:
            raise ValueError("No se recibio JSON valido.")
        return {}
    if not isinstance(payload, dict):
        raise ValueError("El cuerpo JSON debe ser un objeto.")
    return payload


def _dni_data_node(payload: Dict[str, Any]) -> Dict[str, Any]:
    for key in ("data", "persona", "person", "result", "resultado"):
        value = payload.get(key)
        if isinstance(value, dict):
            return value
        if isinstance(value, list) and value and isinstance(value[0], dict):
            return value[0]
    return payload


def _normalize_key(value: str) -> str:
    return "".join(char for char in value.lower() if char.isalnum())


def _lookup_value(data: Dict[str, Any], *keys: str) -> str:
    if not isinstance(data, dict):
        return ""
    normalized = {_normalize_key(str(key)): value for key, value in data.items()}
    for key in keys:
        value = normalized.get(_normalize_key(key))
        if value not in (None, ""):
            return str(value).strip()
    return ""


def _split_full_name(full_name: str) -> tuple[str, str]:
    parts = [part for part in str(full_name or "").strip().split() if part]
    if len(parts) >= 4:
        return " ".join(parts[2:]), " ".join(parts[:2])
    if len(parts) == 3:
        return parts[2], " ".join(parts[:2])
    if len(parts) == 2:
        return parts[0], parts[1]
    return full_name.strip(), ""


def _extract_birth_date(data: Dict[str, Any]) -> date | None:
    raw_value = _lookup_value(
        data,
        "fecha_nacimiento",
        "fechaNacimiento",
        "fecha_de_nacimiento",
        "fec_nacimiento",
        "fecNacimiento",
        "fecha_nac",
        "fecnac",
        "nacimiento",
        "birth_date",
        "birthDate",
    )
    if not raw_value:
        return None

    text = str(raw_value).strip()
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%Y/%m/%d"):
        try:
            return datetime.strptime(text[:10], fmt).date()
        except ValueError:
            continue
    return None


def _calculate_age(birth_date: date) -> int:
    today = date.today()
    years = today.year - birth_date.year
    if (today.month, today.day) < (birth_date.month, birth_date.day):
        years -= 1
    return max(0, years)


def _normalize_sex(value: Any) -> str:
    text = str(value or "").strip().upper()
    if text in {"M", "1", "MASCULINO", "HOMBRE", "MALE"}:
        return "Masculino"
    if text in {"F", "2", "FEMENINO", "MUJER", "FEMALE"}:
        return "Femenino"
    return "No especificado"


def _normalize_vitals(payload: Dict[str, Any]) -> Dict[str, Any]:
    def number(*keys: str, default: float = 0.0) -> float:
        for key in keys:
            value = payload.get(key)
            if value is not None and value != "":
                return float(value)
        return default

    def blood_pressure(default_systolic: int = 120, default_diastolic: int = 80) -> tuple[int, int]:
        systolic = int(
            round(number("blood_pressure_systolic", "systolic", "sistolica", default=default_systolic))
        )
        diastolic = int(
            round(number("blood_pressure_diastolic", "diastolic", "diastolica", default=default_diastolic))
        )
        combined = payload.get("blood_pressure") or payload.get("pressure") or payload.get("presion")
        if combined and (
            payload.get("blood_pressure_systolic") in {None, ""}
            or payload.get("blood_pressure_diastolic") in {None, ""}
        ):
            clean_value = str(combined).replace("mmHg", "").replace(" ", "")
            separator = "/" if "/" in clean_value else "-"
            parts = clean_value.split(separator, 1)
            if len(parts) == 2:
                systolic = int(round(float(parts[0])))
                diastolic = int(round(float(parts[1])))
        return systolic, diastolic

    systolic, diastolic = blood_pressure()

    vitals = {
        "temperatura": round(number("temperature", "temperatura", default=0.0) or 36.5, 1),
        "ritmo_cardiaco": int(round(number("heart_rate", "ritmo_cardiaco", default=0.0) or 75)),
        "spO2": int(round(number("spO2", "spo2", "saturation", default=0.0) or 98)),
        "blood_pressure_sistolica": systolic,
        "blood_pressure_diastolica": diastolic,
        "peso": round(number("weight", "peso", default=0.0) or 70.0, 1),
        "altura": round(number("height", "altura", "talla", default=0.0) or 170.0, 1),
    }
    return vitals


app = create_app()



if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True, port=int(os.getenv("PORT", "5000")))




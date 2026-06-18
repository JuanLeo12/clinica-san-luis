from __future__ import annotations

import json
import os
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

import requests


DEFAULT_SPECIALTIES = [
    {
        "id": 1,
        "name": "Medicina General",
        "price": 55.0,
        "duration_min": 20,
        "room": "C-101",
        "doctor_name": "Dra. Valeria Ramos",
    },
    {
        "id": 2,
        "name": "Pediatria",
        "price": 70.0,
        "duration_min": 20,
        "room": "C-102",
        "doctor_name": "Dr. Mateo Aguilar",
    },
    {
        "id": 3,
        "name": "Cardiologia",
        "price": 120.0,
        "duration_min": 30,
        "room": "C-201",
        "doctor_name": "Dra. Camila Torres",
    },
    {
        "id": 4,
        "name": "Dermatologia",
        "price": 90.0,
        "duration_min": 20,
        "room": "C-202",
        "doctor_name": "Dr. Alonso Vega",
    },
    {
        "id": 5,
        "name": "Ginecologia",
        "price": 100.0,
        "duration_min": 25,
        "room": "C-203",
        "doctor_name": "Dra. Sofia Paredes",
    },
    {
        "id": 6,
        "name": "Traumatologia",
        "price": 110.0,
        "duration_min": 25,
        "room": "C-204",
        "doctor_name": "Dr. Diego Salazar",
    },
]
DEFAULT_USERS = [
    {"id": 1, "username": "admin", "password": "admin123", "full_name": "Administrador", "role": "admin"},
    {"id": 2, "username": "recep", "password": "recep123", "full_name": "Maria Lopez", "role": "reception"},
    {"id": 3, "username": "caja", "password": "caja123", "full_name": "Carlos Perez", "role": "cashier"},
    {"id": 4, "username": "triage", "password": "triage123", "full_name": "Ana Torres", "role": "triage"},
    {"id": 5, "username": "doctor", "password": "doctor123", "full_name": "Dr. Roberto Silva", "role": "doctor"},
    {"id": 6, "username": "farmacia", "password": "farm123", "full_name": "Laura Gomez", "role": "pharmacy"},
]
def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def local_now() -> datetime:
    return datetime.now()


def _clean_digits(value: Any) -> str:
    return "".join(char for char in str(value or "").strip() if char.isdigit())


def _validate_document(value: Any, label: str = "DNI") -> str:
    document = _clean_digits(value)
    if len(document) != 8:
        raise ValueError(f"{label} debe tener 8 digitos.")
    return document


def _validate_phone(value: Any) -> str:
    phone = _clean_digits(value)
    if len(phone) != 9:
        raise ValueError("Telefono debe tener 9 digitos y no aceptar letras.")
    return phone


def _required_text(value: Any, label: str) -> str:
    text = str(value or "").strip()
    if not text:
        raise ValueError(f"{label} es obligatorio.")
    return text


def _validate_age(value: Any) -> int:
    age = int(value or 0)
    if age < 1 or age > 120:
        raise ValueError("Edad debe estar entre 1 y 120.")
    return age


def _optional_age(value: Any) -> Optional[int]:
    if value in (None, ""):
        return None
    return _validate_age(value)


def _optional_date_text(value: Any) -> str:
    return str(value or "").strip()[:10]


def _validate_patient_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "document": _validate_document(payload.get("document")),
        "first_name": _required_text(payload.get("first_name"), "Nombres"),
        "last_name": _required_text(payload.get("last_name"), "Apellidos"),
        "age": _validate_age(payload.get("age")),
        "sex": _required_text(payload.get("sex") or "No especificado", "Sexo"),
        "phone": _validate_phone(payload.get("phone")),
        "birth_date": _optional_date_text(payload.get("birth_date")),
    }


def _validate_worker_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    role = _required_text(payload.get("role"), "Rol")
    specialty = str(payload.get("specialty") or "").strip()
    if role == "doctor" and not specialty:
        raise ValueError("Especialidad es obligatoria para trabajadores medicos.")
    return {
        "document": _validate_document(payload.get("document")),
        "first_name": _required_text(payload.get("first_name"), "Nombres"),
        "last_name": _required_text(payload.get("last_name"), "Apellidos"),
        "role": role,
        "specialty": specialty if role == "doctor" else "",
        "phone": _validate_phone(payload.get("phone")),
        "age": _optional_age(payload.get("age")),
        "sex": _required_text(payload.get("sex") or "No especificado", "Sexo"),
        "birth_date": _optional_date_text(payload.get("birth_date")),
    }


def create_repository() -> "BaseRepository":
    storage_mode = os.getenv("APP_STORAGE", "sqlite").lower()
    if storage_mode == "supabase":
        return SupabaseRepository(
            url=os.environ["SUPABASE_URL"],
            key=os.environ["SUPABASE_SERVICE_ROLE_KEY"],
        )
    db_path = os.getenv("DATABASE_PATH")
    if not db_path:
        db_path = "/tmp/clinic_app.sqlite3" if os.getenv("VERCEL") else "clinic_app.sqlite3"
    return SQLiteRepository(db_path)


class BaseRepository:
    def setup(self) -> None:
        raise NotImplementedError

    def snapshot(self) -> Dict[str, Any]:
        raise NotImplementedError

    def list_specialties(self) -> List[Dict[str, Any]]:
        raise NotImplementedError

    def get_appointment(self, appointment_id: int) -> Optional[Dict[str, Any]]:
        raise NotImplementedError

    def create_patient_and_appointment(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        raise NotImplementedError

    def mark_paid(
        self,
        appointment_id: int,
        payment_method: str = "Efectivo",
        created_by: Optional[str] = None,
    ) -> Dict[str, Any]:
        raise NotImplementedError

    def set_active_triage(self, appointment_id: int) -> Dict[str, Any]:
        raise NotImplementedError

    def capture_triage(
        self,
        appointment_id: int,
        vitals: Dict[str, Any],
        analysis: Dict[str, Any],
        source: str,
    ) -> Dict[str, Any]:
        raise NotImplementedError

    def create_consultation(self, appointment_id: int, payload: Dict[str, Any]) -> Dict[str, Any]:
        raise NotImplementedError

    def dispense_prescription(
        self,
        prescription_id: int,
        payment_method: str = "Efectivo",
        created_by: Optional[str] = None,
    ) -> Dict[str, Any]:
        raise NotImplementedError

    def list_transactions(self) -> List[Dict[str, Any]]:
        raise NotImplementedError

    def get_setting(self, key: str) -> Optional[str]:
        raise NotImplementedError

    def set_setting(self, key: str, value: Optional[str]) -> None:
        raise NotImplementedError

    def authenticate_user(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        raise NotImplementedError

    def list_users(self) -> List[Dict[str, Any]]:
        raise NotImplementedError


class SQLiteRepository(BaseRepository):
    def __init__(self, db_path: str) -> None:
        self.db_path = Path(db_path)

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    def setup(self) -> None:
        with self._connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS patients (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    document TEXT NOT NULL UNIQUE,
                    first_name TEXT NOT NULL,
                    last_name TEXT NOT NULL,
                    age INTEGER NOT NULL,
                    sex TEXT NOT NULL,
                    birth_date TEXT,
                    phone TEXT,
                    active INTEGER NOT NULL DEFAULT 1,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS specialties (
                    id INTEGER PRIMARY KEY,
                    name TEXT NOT NULL,
                    price REAL NOT NULL,
                    duration_min INTEGER NOT NULL,
                    room TEXT NOT NULL,
                    doctor_name TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS appointments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ticket TEXT NOT NULL UNIQUE,
                    patient_id INTEGER NOT NULL REFERENCES patients(id),
                    specialty_id INTEGER NOT NULL REFERENCES specialties(id),
                    status TEXT NOT NULL,
                    payment_status TEXT NOT NULL,
                    triage_status TEXT NOT NULL,
                    consultation_status TEXT NOT NULL,
                    pharmacy_status TEXT NOT NULL,
                    room TEXT,
                    scheduled_at TEXT,
                    receipt_code TEXT,
                    created_at TEXT NOT NULL,
                    paid_at TEXT
                );

                CREATE TABLE IF NOT EXISTS triage_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    appointment_id INTEGER NOT NULL UNIQUE REFERENCES appointments(id),
                    temperature REAL NOT NULL,
                    heart_rate INTEGER NOT NULL,
                    spo2 INTEGER NOT NULL,
                    systolic INTEGER NOT NULL,
                    diastolic INTEGER NOT NULL,
                    weight REAL NOT NULL,
                    height REAL NOT NULL,
                    bmi REAL NOT NULL,
                    priority TEXT NOT NULL,
                    risk_score REAL NOT NULL,
                    risk_label TEXT NOT NULL,
                    predicted_systolic REAL NOT NULL,
                    estimated_attention_minutes REAL NOT NULL,
                    decision_summary TEXT NOT NULL,
                    analysis_json TEXT NOT NULL,
                    source TEXT NOT NULL,
                    captured_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS consultations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    appointment_id INTEGER NOT NULL UNIQUE REFERENCES appointments(id),
                    doctor_name TEXT NOT NULL,
                    symptoms TEXT NOT NULL,
                    diagnosis TEXT NOT NULL,
                    treatment_notes TEXT NOT NULL,
                    notes TEXT,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS prescriptions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    appointment_id INTEGER NOT NULL REFERENCES appointments(id),
                    consultation_id INTEGER NOT NULL REFERENCES consultations(id),
                    status TEXT NOT NULL,
                    total REAL NOT NULL,
                    created_at TEXT NOT NULL,
                    dispensed_at TEXT
                );

                CREATE TABLE IF NOT EXISTS prescription_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    prescription_id INTEGER NOT NULL REFERENCES prescriptions(id) ON DELETE CASCADE,
                    medicine TEXT NOT NULL,
                    dosage TEXT NOT NULL,
                    frequency TEXT NOT NULL,
                    days INTEGER NOT NULL,
                    quantity INTEGER NOT NULL,
                    unit_price REAL NOT NULL
                );

                CREATE TABLE IF NOT EXISTS transactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    transaction_code TEXT NOT NULL UNIQUE,
                    module TEXT NOT NULL,
                    reference_type TEXT NOT NULL,
                    reference_id INTEGER NOT NULL,
                    patient_document TEXT NOT NULL,
                    patient_name TEXT NOT NULL,
                    concept TEXT NOT NULL,
                    amount REAL NOT NULL,
                    payment_method TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_by TEXT,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT NOT NULL UNIQUE,
                    password TEXT NOT NULL,
                    full_name TEXT NOT NULL,
                    role TEXT NOT NULL,
                    active INTEGER NOT NULL DEFAULT 1,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT
                );

                CREATE TABLE IF NOT EXISTS audit_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_type TEXT NOT NULL,
                    entity TEXT NOT NULL,
                    entity_id INTEGER,
                    message TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS workers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    document TEXT NOT NULL UNIQUE,
                    first_name TEXT NOT NULL,
                    last_name TEXT NOT NULL,
                    role TEXT NOT NULL,
                    specialty TEXT,
                    age INTEGER,
                    sex TEXT DEFAULT 'No especificado',
                    birth_date TEXT,
                    phone TEXT,
                    active INTEGER DEFAULT 1,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS consultorios (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    floor TEXT,
                    equipment TEXT,
                    active INTEGER DEFAULT 1,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS medications (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    description TEXT,
                    price REAL DEFAULT 0,
                    stock INTEGER DEFAULT 0,
                    active INTEGER DEFAULT 1,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS workers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    document TEXT NOT NULL UNIQUE,
                    first_name TEXT NOT NULL,
                    last_name TEXT NOT NULL,
                    role TEXT NOT NULL,
                    specialty TEXT,
                    phone TEXT,
                    active INTEGER DEFAULT 1,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS consultorios (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    floor TEXT,
                    equipment TEXT,
                    active INTEGER DEFAULT 1,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS medications (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    description TEXT,
                    price REAL DEFAULT 0,
                    stock INTEGER DEFAULT 0,
                    active INTEGER DEFAULT 1,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS workers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    document TEXT NOT NULL UNIQUE,
                    first_name TEXT NOT NULL,
                    last_name TEXT NOT NULL,
                    role TEXT NOT NULL,
                    specialty TEXT,
                    phone TEXT,
                    active INTEGER DEFAULT 1,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS consultorios (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    floor TEXT,
                    equipment TEXT,
                    active INTEGER DEFAULT 1,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS medications (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    description TEXT,
                    price REAL DEFAULT 0,
                    stock INTEGER DEFAULT 0,
                    active INTEGER DEFAULT 1,
                    created_at TEXT NOT NULL
                );

                """
            )
            patient_columns = {
                row["name"] for row in conn.execute("PRAGMA table_info(patients)").fetchall()
            }
            if "active" not in patient_columns:
                conn.execute("ALTER TABLE patients ADD COLUMN active INTEGER NOT NULL DEFAULT 1")
            if "birth_date" not in patient_columns:
                conn.execute("ALTER TABLE patients ADD COLUMN birth_date TEXT")

            worker_columns = {
                row["name"] for row in conn.execute("PRAGMA table_info(workers)").fetchall()
            }
            if "age" not in worker_columns:
                conn.execute("ALTER TABLE workers ADD COLUMN age INTEGER")
            if "sex" not in worker_columns:
                conn.execute("ALTER TABLE workers ADD COLUMN sex TEXT DEFAULT 'No especificado'")
            if "birth_date" not in worker_columns:
                conn.execute("ALTER TABLE workers ADD COLUMN birth_date TEXT")
            existing = conn.execute("SELECT COUNT(*) FROM specialties").fetchone()[0]
            if existing == 0:
                conn.executemany(
                    """
                    INSERT INTO specialties (id, name, price, duration_min, room, doctor_name)
                    VALUES (:id, :name, :price, :duration_min, :room, :doctor_name)
                    """,
                    DEFAULT_SPECIALTIES,
                )
            existing_user = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
            if existing_user == 0:
                conn.executemany(
                    """
                    INSERT INTO users (id, username, password, full_name, role, active, created_at)
                    VALUES (:id, :username, :password, :full_name, :role, :active, :created_at)
                    """,
                    [
                        {"id": 1, "username": "admin", "password": "admin123", "full_name": "Administrador", "role": "admin", "active": 1, "created_at": utc_now()},
                        {"id": 2, "username": "recep", "password": "recep123", "full_name": "Maria Lopez", "role": "reception", "active": 1, "created_at": utc_now()},
                        {"id": 3, "username": "caja", "password": "caja123", "full_name": "Carlos Perez", "role": "cashier", "active": 1, "created_at": utc_now()},
                        {"id": 4, "username": "triage", "password": "triage123", "full_name": "Ana Torres", "role": "triage", "active": 1, "created_at": utc_now()},
                        {"id": 5, "username": "doctor", "password": "doctor123", "full_name": "Dr. Roberto Silva", "role": "doctor", "active": 1, "created_at": utc_now()},
                        {"id": 6, "username": "farmacia", "password": "farm123", "full_name": "Laura Gomez", "role": "pharmacy", "active": 1, "created_at": utc_now()},
                    ],
                )
            if conn.execute("SELECT COUNT(*) FROM workers").fetchone()[0] == 0:
                conn.executemany(
                    """
                    INSERT INTO workers (document, first_name, last_name, role, specialty, phone, active, created_at)
                    VALUES (:document, :first_name, :last_name, :role, :specialty, :phone, 1, :created_at)
                    """,
                    [
                        {"document": "44556677", "first_name": "Valeria", "last_name": "Ramos", "role": "doctor", "specialty": "Medicina General", "phone": "987654321", "created_at": utc_now()},
                        {"document": "45678912", "first_name": "Mateo", "last_name": "Aguilar", "role": "doctor", "specialty": "Pediatria", "phone": "987111222", "created_at": utc_now()},
                        {"document": "47889900", "first_name": "Ana", "last_name": "Torres", "role": "triage", "specialty": "Enfermeria", "phone": "986222333", "created_at": utc_now()},
                        {"document": "48990011", "first_name": "Maria", "last_name": "Lopez", "role": "reception", "specialty": "", "phone": "985333444", "created_at": utc_now()},
                        {"document": "49001122", "first_name": "Carlos", "last_name": "Perez", "role": "cashier", "specialty": "", "phone": "984444555", "created_at": utc_now()},
                        {"document": "50112233", "first_name": "Laura", "last_name": "Gomez", "role": "pharmacy", "specialty": "Farmacia", "phone": "983555666", "created_at": utc_now()},
                    ],
                )
            if conn.execute("SELECT COUNT(*) FROM consultorios").fetchone()[0] == 0:
                conn.executemany(
                    """
                    INSERT INTO consultorios (name, floor, equipment, active, created_at)
                    VALUES (:name, :floor, :equipment, 1, :created_at)
                    """,
                    [
                        {"name": "C-101", "floor": "Piso 1", "equipment": "Camilla, tensiometro, PC", "created_at": utc_now()},
                        {"name": "C-102", "floor": "Piso 1", "equipment": "Pediatria, balanza pediatrica", "created_at": utc_now()},
                        {"name": "C-201", "floor": "Piso 2", "equipment": "ECG, monitor cardiaco", "created_at": utc_now()},
                        {"name": "Triage 01", "floor": "Piso 1", "equipment": "IoT signos vitales, oximetro", "created_at": utc_now()},
                    ],
                )
            if conn.execute("SELECT COUNT(*) FROM medications").fetchone()[0] == 0:
                conn.executemany(
                    """
                    INSERT INTO medications (name, description, price, stock, active, created_at)
                    VALUES (:name, :description, :price, :stock, 1, :created_at)
                    """,
                    [
                        {"name": "Paracetamol 500 mg", "description": "Analgesico y antipiretico", "price": 1.50, "stock": 120, "created_at": utc_now()},
                        {"name": "Ibuprofeno 400 mg", "description": "Antiinflamatorio", "price": 2.20, "stock": 80, "created_at": utc_now()},
                        {"name": "Amoxicilina 500 mg", "description": "Antibiotico", "price": 3.80, "stock": 60, "created_at": utc_now()},
                        {"name": "Loratadina 10 mg", "description": "Antihistaminico", "price": 1.80, "stock": 90, "created_at": utc_now()},
                        {"name": "Suero oral", "description": "Rehidratacion oral", "price": 4.50, "stock": 45, "created_at": utc_now()},
                    ],
                )
            if conn.execute("SELECT COUNT(*) FROM patients").fetchone()[0] == 0:
                conn.executemany(
                    """
                    INSERT INTO patients (document, first_name, last_name, age, sex, phone, active, created_at)
                    VALUES (:document, :first_name, :last_name, :age, :sex, :phone, 1, :created_at)
                    """,
                    [
                        {"document": "70123456", "first_name": "Lucia", "last_name": "Herrera", "age": 28, "sex": "Femenino", "phone": "999111222", "created_at": utc_now()},
                        {"document": "70456789", "first_name": "Jorge", "last_name": "Salinas", "age": 46, "sex": "Masculino", "phone": "999333444", "created_at": utc_now()},
                        {"document": "70890123", "first_name": "Elena", "last_name": "Quispe", "age": 67, "sex": "Femenino", "phone": "999555666", "created_at": utc_now()},
                    ],
                )
                rows = conn.execute("SELECT id FROM patients ORDER BY id").fetchall()
                demo_appointments = [
                    ("A0001", rows[0]["id"], 1, "registered", "pending", "not_started", "not_started", "none"),
                    ("A0002", rows[1]["id"], 3, "paid", "paid", "waiting", "not_started", "none"),
                    ("A0003", rows[2]["id"], 1, "triaged", "paid", "done", "waiting", "none"),
                ]
                conn.executemany(
                    """
                    INSERT INTO appointments (
                        ticket, patient_id, specialty_id, status, payment_status, triage_status,
                        consultation_status, pharmacy_status, room, scheduled_at, receipt_code, created_at, paid_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'C-101', ?, 'B-DEMO', ?, ?)
                    """,
                    [
                        (
                            ticket,
                            patient_id,
                            specialty_id,
                            status,
                            payment_status,
                            triage_status,
                            consultation_status,
                            pharmacy_status,
                            local_now().isoformat(timespec="minutes"),
                            utc_now(),
                            utc_now() if payment_status == "paid" else None,
                        )
                        for ticket, patient_id, specialty_id, status, payment_status, triage_status, consultation_status, pharmacy_status in demo_appointments
                    ],
                )
            self._seed_demo_data(conn)

    def _seed_demo_data(self, conn: sqlite3.Connection) -> None:
        specialties = {
            row["id"]: dict(row)
            for row in conn.execute("SELECT * FROM specialties").fetchall()
        }

        def ensure_patient(payload: Dict[str, Any]) -> int:
            existing = conn.execute(
                "SELECT id FROM patients WHERE document = ?", (payload["document"],)
            ).fetchone()
            if existing:
                conn.execute(
                    """
                    UPDATE patients
                    SET first_name = COALESCE(NULLIF(first_name, ''), :first_name),
                        last_name = COALESCE(NULLIF(last_name, ''), :last_name),
                        age = COALESCE(age, :age),
                        sex = COALESCE(NULLIF(sex, ''), :sex),
                        birth_date = COALESCE(NULLIF(birth_date, ''), :birth_date),
                        phone = COALESCE(NULLIF(phone, ''), :phone),
                        active = 1
                    WHERE id = :id
                    """,
                    {**payload, "id": existing["id"]},
                )
                return int(existing["id"])

            cursor = conn.execute(
                """
                INSERT INTO patients (
                    document, first_name, last_name, age, sex, birth_date, phone, active, created_at
                )
                VALUES (:document, :first_name, :last_name, :age, :sex, :birth_date, :phone, 1, :created_at)
                """,
                {**payload, "created_at": utc_now()},
            )
            return int(cursor.lastrowid)

        demo_patients = {
            "Rosa": ensure_patient(
                {
                    "document": "70987654",
                    "first_name": "Rosa",
                    "last_name": "Medina Torres",
                    "age": 34,
                    "sex": "Femenino",
                    "birth_date": "1992-04-13",
                    "phone": "997123456",
                }
            ),
            "Miguel": ensure_patient(
                {
                    "document": "71345678",
                    "first_name": "Miguel",
                    "last_name": "Castro Leon",
                    "age": 52,
                    "sex": "Masculino",
                    "birth_date": "1974-02-09",
                    "phone": "996234567",
                }
            ),
            "Carmen": ensure_patient(
                {
                    "document": "72456789",
                    "first_name": "Carmen",
                    "last_name": "Flores Rivas",
                    "age": 71,
                    "sex": "Femenino",
                    "birth_date": "1955-11-21",
                    "phone": "995345678",
                }
            ),
            "Diego": ensure_patient(
                {
                    "document": "73567890",
                    "first_name": "Diego",
                    "last_name": "Rojas Vega",
                    "age": 39,
                    "sex": "Masculino",
                    "birth_date": "1987-07-02",
                    "phone": "994456789",
                }
            ),
            "Patricia": ensure_patient(
                {
                    "document": "74678901",
                    "first_name": "Patricia",
                    "last_name": "Nunez Soto",
                    "age": 29,
                    "sex": "Femenino",
                    "birth_date": "1997-09-18",
                    "phone": "993567890",
                }
            ),
        }

        def ensure_appointment(
            ticket: str,
            patient_id: int,
            specialty_id: int,
            status: str,
            payment_status: str,
            triage_status: str,
            consultation_status: str,
            pharmacy_status: str,
            minutes_ahead: int,
        ) -> int:
            existing = conn.execute(
                "SELECT id FROM appointments WHERE ticket = ?", (ticket,)
            ).fetchone()
            if existing:
                return int(existing["id"])

            specialty = specialties[specialty_id]
            paid = payment_status == "paid"
            cursor = conn.execute(
                """
                INSERT INTO appointments (
                    ticket, patient_id, specialty_id, status, payment_status, triage_status,
                    consultation_status, pharmacy_status, room, scheduled_at, receipt_code, created_at, paid_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    ticket,
                    patient_id,
                    specialty_id,
                    status,
                    payment_status,
                    triage_status,
                    consultation_status,
                    pharmacy_status,
                    specialty["room"] if paid else None,
                    (local_now() + timedelta(minutes=minutes_ahead)).isoformat(timespec="minutes")
                    if paid
                    else None,
                    f"B-DEMO-{ticket}" if paid else None,
                    utc_now(),
                    utc_now() if paid else None,
                ),
            )
            return int(cursor.lastrowid)

        appointments = {
            "A0101": ensure_appointment(
                "A0101", demo_patients["Rosa"], 1, "registered", "pending",
                "not_started", "not_started", "none", 0
            ),
            "A0102": ensure_appointment(
                "A0102", demo_patients["Miguel"], 3, "paid", "paid",
                "waiting", "not_started", "none", 20
            ),
            "A0103": ensure_appointment(
                "A0103", demo_patients["Carmen"], 1, "triaged", "paid",
                "done", "waiting", "none", 35
            ),
            "A0104": ensure_appointment(
                "A0104", demo_patients["Diego"], 4, "prescription_pending", "paid",
                "done", "done", "pending", 50
            ),
            "A0105": ensure_appointment(
                "A0105", demo_patients["Patricia"], 2, "completed", "paid",
                "done", "done", "dispensed", 65
            ),
        }

        def ensure_triage(appointment_id: int, vitals: Dict[str, Any], analysis: Dict[str, Any]) -> None:
            existing = conn.execute(
                "SELECT id FROM triage_records WHERE appointment_id = ?", (appointment_id,)
            ).fetchone()
            if existing:
                return
            conn.execute(
                """
                INSERT INTO triage_records (
                    appointment_id, temperature, heart_rate, spo2, systolic, diastolic,
                    weight, height, bmi, priority, risk_score, risk_label,
                    predicted_systolic, estimated_attention_minutes, decision_summary,
                    analysis_json, source, captured_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'Demo IoT', ?)
                """,
                (
                    appointment_id,
                    vitals["temperature"],
                    vitals["heart_rate"],
                    vitals["spo2"],
                    vitals["systolic"],
                    vitals["diastolic"],
                    vitals["weight"],
                    vitals["height"],
                    analysis["bmi"],
                    analysis["priority"],
                    analysis["risk_probability"],
                    analysis["risk_label"],
                    analysis["predicted_systolic"],
                    analysis["estimated_attention_minutes"],
                    analysis["decision_summary"],
                    json.dumps(analysis),
                    utc_now(),
                ),
            )

        base_algorithms = {
            "linear_regression": "Presion sistolica esperada por frecuencia cardiaca.",
            "multiple_linear_regression": "Minutos estimados por edad, signos vitales e IMC.",
            "logistic_regression": "Probabilidad de riesgo clinico.",
            "decision_tree": "Prioridad operativa para la cola medica.",
        }
        ensure_triage(
            appointments["A0103"],
            {
                "temperature": 38.4,
                "heart_rate": 112,
                "spo2": 94,
                "systolic": 146,
                "diastolic": 88,
                "weight": 73.0,
                "height": 154.0,
            },
            {
                "bmi": 30.78,
                "risk_probability": 0.68,
                "risk_label": "Moderado",
                "priority": "Urgente",
                "predicted_systolic": 139.4,
                "estimated_attention_minutes": 24.0,
                "flags": ["Fiebre", "Frecuencia cardiaca alta", "Saturacion baja"],
                "decision_summary": "Urgente por fiebre, frecuencia cardiaca alta y saturacion baja. Riesgo moderado.",
                "algorithms": base_algorithms,
            },
        )
        ensure_triage(
            appointments["A0104"],
            {
                "temperature": 37.1,
                "heart_rate": 86,
                "spo2": 97,
                "systolic": 126,
                "diastolic": 79,
                "weight": 84.0,
                "height": 172.0,
            },
            {
                "bmi": 28.39,
                "risk_probability": 0.24,
                "risk_label": "Bajo",
                "priority": "Rutina",
                "predicted_systolic": 127.1,
                "estimated_attention_minutes": 15.5,
                "flags": [],
                "decision_summary": "Rutina. Signos dentro de rango operativo. Riesgo bajo.",
                "algorithms": base_algorithms,
            },
        )
        ensure_triage(
            appointments["A0105"],
            {
                "temperature": 36.8,
                "heart_rate": 92,
                "spo2": 98,
                "systolic": 120,
                "diastolic": 76,
                "weight": 62.0,
                "height": 161.0,
            },
            {
                "bmi": 23.92,
                "risk_probability": 0.18,
                "risk_label": "Bajo",
                "priority": "Rutina",
                "predicted_systolic": 129.6,
                "estimated_attention_minutes": 14.0,
                "flags": [],
                "decision_summary": "Rutina. Signos dentro de rango operativo. Riesgo bajo.",
                "algorithms": base_algorithms,
            },
        )

        def ensure_consultation(
            appointment_id: int,
            doctor_name: str,
            symptoms: str,
            diagnosis: str,
            treatment_notes: str,
        ) -> int:
            existing = conn.execute(
                "SELECT id FROM consultations WHERE appointment_id = ?", (appointment_id,)
            ).fetchone()
            if existing:
                return int(existing["id"])
            cursor = conn.execute(
                """
                INSERT INTO consultations (
                    appointment_id, doctor_name, symptoms, diagnosis, treatment_notes, notes, created_at
                )
                VALUES (?, ?, ?, ?, ?, '', ?)
                """,
                (appointment_id, doctor_name, symptoms, diagnosis, treatment_notes, utc_now()),
            )
            return int(cursor.lastrowid)

        consultation_a0104 = ensure_consultation(
            appointments["A0104"],
            "Dr. Alonso Vega",
            "Lesiones pruriginosas en antebrazo desde hace 3 dias.",
            "Dermatitis alergica leve",
            "Evitar irritantes, antihistaminico y control si progresa.",
        )
        consultation_a0105 = ensure_consultation(
            appointments["A0105"],
            "Dr. Mateo Aguilar",
            "Dolor de garganta y fiebre referida.",
            "Faringitis aguda",
            "Reposo, hidratacion y analgesico segun dolor.",
        )

        def ensure_prescription(
            appointment_id: int,
            consultation_id: int,
            status: str,
            dispensed: bool,
            items: Sequence[Dict[str, Any]],
        ) -> int:
            existing = conn.execute(
                "SELECT id FROM prescriptions WHERE appointment_id = ?", (appointment_id,)
            ).fetchone()
            if existing:
                return int(existing["id"])
            total = sum(float(item["unit_price"]) * int(item["quantity"]) for item in items)
            cursor = conn.execute(
                """
                INSERT INTO prescriptions (
                    appointment_id, consultation_id, status, total, created_at, dispensed_at
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    appointment_id,
                    consultation_id,
                    status,
                    total,
                    utc_now(),
                    utc_now() if dispensed else None,
                ),
            )
            prescription_id = int(cursor.lastrowid)
            conn.executemany(
                """
                INSERT INTO prescription_items (
                    prescription_id, medicine, dosage, frequency, days, quantity, unit_price
                )
                VALUES (:prescription_id, :medicine, :dosage, :frequency, :days, :quantity, :unit_price)
                """,
                [dict(item, prescription_id=prescription_id) for item in items],
            )
            return prescription_id

        prescription_a0104 = ensure_prescription(
            appointments["A0104"],
            consultation_a0104,
            "pending",
            False,
            [
                {
                    "medicine": "Loratadina 10 mg",
                    "dosage": "1 tableta",
                    "frequency": "Cada 24 horas",
                    "days": 5,
                    "quantity": 5,
                    "unit_price": 1.80,
                },
                {
                    "medicine": "Paracetamol 500 mg",
                    "dosage": "1 tableta",
                    "frequency": "Si hay dolor",
                    "days": 3,
                    "quantity": 6,
                    "unit_price": 1.50,
                },
            ],
        )
        prescription_a0105 = ensure_prescription(
            appointments["A0105"],
            consultation_a0105,
            "dispensed",
            True,
            [
                {
                    "medicine": "Paracetamol 500 mg",
                    "dosage": "1 tableta",
                    "frequency": "Cada 8 horas",
                    "days": 3,
                    "quantity": 9,
                    "unit_price": 1.50,
                },
                {
                    "medicine": "Suero oral",
                    "dosage": "1 sobre",
                    "frequency": "Segun tolerancia",
                    "days": 2,
                    "quantity": 2,
                    "unit_price": 4.50,
                },
            ],
        )

        self._backfill_transactions(conn)
        prescription = conn.execute(
            """
            SELECT pr.*, a.ticket, p.document AS patient_document,
                   p.first_name || ' ' || p.last_name AS patient_name
            FROM prescriptions pr
            JOIN appointments a ON a.id = pr.appointment_id
            JOIN patients p ON p.id = a.patient_id
            WHERE pr.id = ?
            """,
            (prescription_a0105,),
        ).fetchone()
        if prescription:
            self._record_transaction(
                conn,
                module="pharmacy",
                reference_type="prescription",
                reference_id=prescription_a0105,
                patient_document=prescription["patient_document"],
                patient_name=prescription["patient_name"],
                concept=f"Medicamentos - {prescription['ticket']}",
                amount=float(prescription["total"] or 0),
                payment_method="Yape",
                created_by="farmacia",
            )

    def _backfill_transactions(self, conn: sqlite3.Connection) -> None:
        paid_appointments = conn.execute(
            """
            SELECT a.id, p.document AS patient_document,
                   p.first_name || ' ' || p.last_name AS patient_name,
                   s.name AS specialty_name, s.price AS specialty_price
            FROM appointments a
            JOIN patients p ON p.id = a.patient_id
            JOIN specialties s ON s.id = a.specialty_id
            WHERE a.payment_status = 'paid'
            """
        ).fetchall()
        for row in paid_appointments:
            self._record_transaction(
                conn,
                module="cashier",
                reference_type="appointment",
                reference_id=int(row["id"]),
                patient_document=row["patient_document"],
                patient_name=row["patient_name"],
                concept=f"Consulta - {row['specialty_name']}",
                amount=float(row["specialty_price"] or 0),
                payment_method="Efectivo",
                created_by="seed",
            )

        dispensed_prescriptions = conn.execute(
            """
            SELECT pr.id, pr.total, a.ticket, p.document AS patient_document,
                   p.first_name || ' ' || p.last_name AS patient_name
            FROM prescriptions pr
            JOIN appointments a ON a.id = pr.appointment_id
            JOIN patients p ON p.id = a.patient_id
            WHERE pr.status = 'dispensed'
            """
        ).fetchall()
        for row in dispensed_prescriptions:
            self._record_transaction(
                conn,
                module="pharmacy",
                reference_type="prescription",
                reference_id=int(row["id"]),
                patient_document=row["patient_document"],
                patient_name=row["patient_name"],
                concept=f"Medicamentos - {row['ticket']}",
                amount=float(row["total"] or 0),
                payment_method="Efectivo",
                created_by="seed",
            )
    def snapshot(self) -> Dict[str, Any]:
        return {
            "specialties": self.list_specialties(),
            "appointments": self.list_appointments(),
            "prescriptions": self.list_prescriptions(),
            "transactions": self.list_transactions(),
            "stats": self.stats(),
            "active_triage_appointment_id": self.get_setting("active_triage_appointment_id"),
            "called_triage_appointment_id": self.get_setting("called_triage_appointment_id"),
            "called_doctor_appointment_id": self.get_setting("called_doctor_appointment_id"),
        }

    def list_specialties(self) -> List[Dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute("SELECT * FROM specialties ORDER BY id").fetchall()
        return [dict(row) for row in rows]

    def list_appointments(self) -> List[Dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT
                    a.*,
                    p.document AS patient_document,
                    p.first_name AS patient_first_name,
                    p.last_name AS patient_last_name,
                    p.age AS patient_age,
                    p.sex AS patient_sex,
                    p.birth_date AS patient_birth_date,
                    p.phone AS patient_phone,
                    s.name AS specialty_name,
                    s.price AS specialty_price,
                    s.duration_min AS specialty_duration_min,
                    s.doctor_name AS specialty_doctor_name
                FROM appointments a
                JOIN patients p ON p.id = a.patient_id
                JOIN specialties s ON s.id = a.specialty_id
                ORDER BY a.id DESC
                """
            ).fetchall()
            triage_rows = conn.execute("SELECT * FROM triage_records").fetchall()
            consultation_rows = conn.execute("SELECT * FROM consultations").fetchall()
        triage_by_appointment = {row["appointment_id"]: self._triage_dict(row) for row in triage_rows}
        consultation_by_appointment = {
            row["appointment_id"]: dict(row) for row in consultation_rows
        }
        return [
            self._appointment_dict(
                row,
                triage_by_appointment.get(row["id"]),
                consultation_by_appointment.get(row["id"]),
            )
            for row in rows
        ]

    def get_appointment(self, appointment_id: int) -> Optional[Dict[str, Any]]:
        return next(
            (item for item in self.list_appointments() if int(item["id"]) == int(appointment_id)),
            None,
        )

    def create_patient_and_appointment(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        patient_data = _validate_patient_payload(payload)
        specialty_id = int(payload.get("specialty_id") or 0)

        if specialty_id <= 0:
            raise ValueError("Faltan datos obligatorios del paciente o especialidad.")

        with self._connect() as conn:
            patient = conn.execute(
                "SELECT id FROM patients WHERE document = ?", (patient_data["document"],)
            ).fetchone()
            if patient:
                patient_id = int(patient["id"])
                conn.execute(
                    """
                    UPDATE patients
                    SET first_name = ?, last_name = ?, age = ?, sex = ?, birth_date = ?, phone = ?
                    WHERE id = ?
                    """,
                    (
                        patient_data["first_name"],
                        patient_data["last_name"],
                        patient_data["age"],
                        patient_data["sex"],
                        patient_data["birth_date"],
                        patient_data["phone"],
                        patient_id,
                    ),
                )
            else:
                cursor = conn.execute(
                    """
                    INSERT INTO patients (
                        document, first_name, last_name, age, sex, birth_date, phone, active, created_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, 1, ?)
                    """,
                    (
                        patient_data["document"],
                        patient_data["first_name"],
                        patient_data["last_name"],
                        patient_data["age"],
                        patient_data["sex"],
                        patient_data["birth_date"],
                        patient_data["phone"],
                        utc_now(),
                    ),
                )
                patient_id = int(cursor.lastrowid)

            ticket = self._next_ticket(conn)
            cursor = conn.execute(
                """
                INSERT INTO appointments (
                    ticket, patient_id, specialty_id, status, payment_status, triage_status,
                    consultation_status, pharmacy_status, created_at
                )
                VALUES (?, ?, ?, 'registered', 'pending', 'not_started', 'not_started', 'none', ?)
                """,
                (ticket, patient_id, specialty_id, utc_now()),
            )
            appointment_id = int(cursor.lastrowid)
            self._audit(conn, "appointment_created", "appointments", appointment_id, f"Cita {ticket} registrada")
        appointment = self.get_appointment(appointment_id)
        if appointment is None:
            raise RuntimeError("No se pudo recuperar la cita creada.")
        return appointment

    def mark_paid(
        self,
        appointment_id: int,
        payment_method: str = "Efectivo",
        created_by: Optional[str] = None,
    ) -> Dict[str, Any]:
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT
                    a.*,
                    p.document AS patient_document,
                    p.first_name || ' ' || p.last_name AS patient_name,
                    s.name AS specialty_name,
                    s.price AS specialty_price,
                    s.room,
                    s.duration_min
                FROM appointments a
                JOIN patients p ON p.id = a.patient_id
                JOIN specialties s ON s.id = a.specialty_id
                WHERE a.id = ?
                """,
                (appointment_id,),
            ).fetchone()
            if row is None:
                raise ValueError("Cita no encontrada.")
            if row["payment_status"] == "paid":
                self._record_transaction(
                    conn,
                    module="cashier",
                    reference_type="appointment",
                    reference_id=appointment_id,
                    patient_document=row["patient_document"],
                    patient_name=row["patient_name"],
                    concept=f"Consulta - {row['specialty_name']}",
                    amount=float(row["specialty_price"] or 0),
                    payment_method=payment_method,
                    created_by=created_by,
                )
            else:
                paid_count = conn.execute(
                    """
                    SELECT COUNT(*) FROM appointments
                    WHERE specialty_id = ? AND payment_status = 'paid'
                    """,
                    (row["specialty_id"],),
                ).fetchone()[0]
                scheduled_at = local_now() + timedelta(minutes=(paid_count + 1) * int(row["duration_min"]))
                receipt_code = f"B{datetime.now().strftime('%Y%m%d%H%M')}-{appointment_id:04d}"
                conn.execute(
                    """
                    UPDATE appointments
                    SET status = 'paid',
                        payment_status = 'paid',
                        triage_status = 'waiting',
                        consultation_status = 'not_started',
                        pharmacy_status = 'none',
                        room = ?,
                        scheduled_at = ?,
                        receipt_code = ?,
                        paid_at = ?
                    WHERE id = ?
                    """,
                    (
                        row["room"],
                        scheduled_at.isoformat(timespec="minutes"),
                        receipt_code,
                        utc_now(),
                        appointment_id,
                    ),
                )
                self._audit(conn, "payment_registered", "appointments", appointment_id, f"Pago {receipt_code} confirmado")
                self._record_transaction(
                    conn,
                    module="cashier",
                    reference_type="appointment",
                    reference_id=appointment_id,
                    patient_document=row["patient_document"],
                    patient_name=row["patient_name"],
                    concept=f"Consulta - {row['specialty_name']}",
                    amount=float(row["specialty_price"] or 0),
                    payment_method=payment_method,
                    created_by=created_by,
                )
        appointment = self.get_appointment(appointment_id)
        if appointment is None:
            raise RuntimeError("No se pudo recuperar la cita pagada.")
        return appointment

    def set_active_triage(self, appointment_id: int) -> Dict[str, Any]:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM appointments WHERE id = ?", (appointment_id,)
            ).fetchone()
            if row is None:
                raise ValueError("Cita no encontrada.")
            if row["payment_status"] != "paid":
                raise ValueError("La cita debe estar pagada antes de triaje.")
            if row["triage_status"] == "done":
                raise ValueError("El triaje ya fue registrado.")

            conn.execute(
                """
                UPDATE appointments
                SET status = 'in_triage', triage_status = 'in_progress'
                WHERE id = ?
                """,
                (appointment_id,),
            )
            self._set_setting(conn, "active_triage_appointment_id", str(appointment_id))
            self._audit(conn, "triage_started", "appointments", appointment_id, "Paciente activado para captura IoT")
        appointment = self.get_appointment(appointment_id)
        if appointment is None:
            raise RuntimeError("No se pudo recuperar la cita activa.")
        return appointment

    def capture_triage(
        self,
        appointment_id: int,
        vitals: Dict[str, Any],
        analysis: Dict[str, Any],
        source: str,
    ) -> Dict[str, Any]:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM appointments WHERE id = ?", (appointment_id,)
            ).fetchone()
            if row is None:
                raise ValueError("Cita no encontrada.")
            captured_at = utc_now()
            conn.execute(
                """
                INSERT INTO triage_records (
                    appointment_id, temperature, heart_rate, spo2, systolic, diastolic,
                    weight, height, bmi, priority, risk_score, risk_label,
                    predicted_systolic, estimated_attention_minutes, decision_summary,
                    analysis_json, source, captured_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(appointment_id) DO UPDATE SET
                    temperature = excluded.temperature,
                    heart_rate = excluded.heart_rate,
                    spo2 = excluded.spo2,
                    systolic = excluded.systolic,
                    diastolic = excluded.diastolic,
                    weight = excluded.weight,
                    height = excluded.height,
                    bmi = excluded.bmi,
                    priority = excluded.priority,
                    risk_score = excluded.risk_score,
                    risk_label = excluded.risk_label,
                    predicted_systolic = excluded.predicted_systolic,
                    estimated_attention_minutes = excluded.estimated_attention_minutes,
                    decision_summary = excluded.decision_summary,
                    analysis_json = excluded.analysis_json,
                    source = excluded.source,
                    captured_at = excluded.captured_at
                """,
                (
                    appointment_id,
                    float(vitals["temperature"]),
                    int(vitals["heart_rate"]),
                    int(vitals["spO2"]),
                    int(vitals["blood_pressure_systolic"]),
                    int(vitals["blood_pressure_diastolic"]),
                    float(vitals["weight"]),
                    float(vitals["height"]),
                    float(analysis["bmi"]),
                    analysis["priority"],
                    float(analysis["risk_probability"]),
                    analysis["risk_label"],
                    float(analysis["predicted_systolic"]),
                    float(analysis["estimated_attention_minutes"]),
                    analysis["decision_summary"],
                    json.dumps(analysis),
                    source,
                    captured_at,
                ),
            )
            next_status = "triaged"
            conn.execute(
                """
                UPDATE appointments
                SET status = ?,
                    triage_status = 'done',
                    consultation_status = 'waiting'
                WHERE id = ?
                """,
                (next_status, appointment_id),
            )
            active = conn.execute(
                "SELECT value FROM settings WHERE key = 'active_triage_appointment_id'"
            ).fetchone()
            if active and active["value"] == str(appointment_id):
                self._set_setting(conn, "active_triage_appointment_id", None)
            self._audit(conn, "triage_captured", "triage_records", appointment_id, f"Triaje {analysis['priority']} registrado")
        appointment = self.get_appointment(appointment_id)
        if appointment is None:
            raise RuntimeError("No se pudo recuperar la cita con triaje.")
        return appointment

    def create_consultation(self, appointment_id: int, payload: Dict[str, Any]) -> Dict[str, Any]:
        symptoms = str(payload.get("symptoms") or "").strip()
        diagnosis = str(payload.get("diagnosis") or "").strip()
        treatment_notes = str(payload.get("treatment_notes") or "").strip()
        notes = str(payload.get("notes") or "").strip()
        doctor_name = str(payload.get("doctor_name") or "").strip()
        items = [item for item in payload.get("prescription_items") or [] if item.get("medicine")]

        if not diagnosis:
            raise ValueError("El diagnostico es obligatorio.")

        with self._connect() as conn:
            appointment = conn.execute(
                """
                SELECT a.*, s.doctor_name
                FROM appointments a
                JOIN specialties s ON s.id = a.specialty_id
                WHERE a.id = ?
                """,
                (appointment_id,),
            ).fetchone()
            if appointment is None:
                raise ValueError("Cita no encontrada.")
            doctor_name = doctor_name or appointment["doctor_name"]

            existing = conn.execute(
                "SELECT id FROM consultations WHERE appointment_id = ?", (appointment_id,)
            ).fetchone()
            if existing:
                consultation_id = int(existing["id"])
                conn.execute(
                    """
                    UPDATE consultations
                    SET doctor_name = ?, symptoms = ?, diagnosis = ?, treatment_notes = ?, notes = ?
                    WHERE id = ?
                    """,
                    (doctor_name, symptoms, diagnosis, treatment_notes, notes, consultation_id),
                )
            else:
                cursor = conn.execute(
                    """
                    INSERT INTO consultations (
                        appointment_id, doctor_name, symptoms, diagnosis, treatment_notes, notes, created_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (appointment_id, doctor_name, symptoms, diagnosis, treatment_notes, notes, utc_now()),
                )
                consultation_id = int(cursor.lastrowid)

            old_prescriptions = conn.execute(
                "SELECT id, status FROM prescriptions WHERE appointment_id = ?", (appointment_id,)
            ).fetchall()
            for old in old_prescriptions:
                if old["status"] != "dispensed":
                    conn.execute("DELETE FROM prescriptions WHERE id = ?", (old["id"],))

            total = 0.0
            prescription_id: Optional[int] = None
            if items:
                normalized_items = []
                for item in items:
                    quantity = max(1, int(item.get("quantity") or 1))
                    unit_price = max(0.0, float(item.get("unit_price") or 0))
                    days = max(1, int(item.get("days") or 1))
                    normalized_items.append(
                        {
                            "medicine": str(item.get("medicine") or "").strip(),
                            "dosage": str(item.get("dosage") or "").strip(),
                            "frequency": str(item.get("frequency") or "").strip(),
                            "days": days,
                            "quantity": quantity,
                            "unit_price": unit_price,
                        }
                    )
                    total += quantity * unit_price

                cursor = conn.execute(
                    """
                    INSERT INTO prescriptions (appointment_id, consultation_id, status, total, created_at)
                    VALUES (?, ?, 'pending', ?, ?)
                    """,
                    (appointment_id, consultation_id, total, utc_now()),
                )
                prescription_id = int(cursor.lastrowid)
                conn.executemany(
                    """
                    INSERT INTO prescription_items (
                        prescription_id, medicine, dosage, frequency, days, quantity, unit_price
                    )
                    VALUES (:prescription_id, :medicine, :dosage, :frequency, :days, :quantity, :unit_price)
                    """,
                    [dict(item, prescription_id=prescription_id) for item in normalized_items],
                )

            pharmacy_status = "pending" if prescription_id else "none"
            status = "prescription_pending" if prescription_id else "completed"
            conn.execute(
                """
                UPDATE appointments
                SET status = ?,
                    consultation_status = 'done',
                    pharmacy_status = ?
                WHERE id = ?
                """,
                (status, pharmacy_status, appointment_id),
            )
            self._audit(conn, "consultation_saved", "consultations", consultation_id, "Consulta medica registrada")
        appointment_data = self.get_appointment(appointment_id)
        if appointment_data is None:
            raise RuntimeError("No se pudo recuperar la consulta.")
        return appointment_data

    def dispense_prescription(
        self,
        prescription_id: int,
        payment_method: str = "Efectivo",
        created_by: Optional[str] = None,
    ) -> Dict[str, Any]:
        with self._connect() as conn:
            prescription = conn.execute(
                """
                SELECT
                    pr.*,
                    a.ticket,
                    p.document AS patient_document,
                    p.first_name || ' ' || p.last_name AS patient_name
                FROM prescriptions pr
                JOIN appointments a ON a.id = pr.appointment_id
                JOIN patients p ON p.id = a.patient_id
                WHERE pr.id = ?
                """,
                (prescription_id,),
            ).fetchone()
            if prescription is None:
                raise ValueError("Receta no encontrada.")
            items = conn.execute(
                "SELECT medicine, quantity FROM prescription_items WHERE prescription_id = ?",
                (prescription_id,),
            ).fetchall()
            conn.execute(
                """
                UPDATE prescriptions
                SET status = 'dispensed', dispensed_at = ?
                WHERE id = ?
                """,
                (utc_now(), prescription_id),
            )
            conn.execute(
                """
                UPDATE appointments
                SET status = 'completed', pharmacy_status = 'dispensed'
                WHERE id = ?
                """,
                (prescription["appointment_id"],),
            )
            for item in items:
                conn.execute(
                    """
                    UPDATE medications
                    SET stock = CASE WHEN stock >= ? THEN stock - ? ELSE 0 END
                    WHERE lower(name) = lower(?) AND active = 1
                    """,
                    (int(item["quantity"]), int(item["quantity"]), item["medicine"]),
                )
            self._record_transaction(
                conn,
                module="pharmacy",
                reference_type="prescription",
                reference_id=prescription_id,
                patient_document=prescription["patient_document"],
                patient_name=prescription["patient_name"],
                concept=f"Medicamentos - {prescription['ticket']}",
                amount=float(prescription["total"] or 0),
                payment_method=payment_method,
                created_by=created_by,
            )
            self._audit(conn, "prescription_dispensed", "prescriptions", prescription_id, "Medicamentos entregados")
        return self.list_prescription(prescription_id)

    def list_prescription(self, prescription_id: int) -> Dict[str, Any]:
        return next(
            item for item in self.list_prescriptions() if int(item["id"]) == int(prescription_id)
        )

    def list_prescriptions(self) -> List[Dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT
                    pr.*,
                    p.first_name || ' ' || p.last_name AS patient_name,
                    p.document AS patient_document,
                    a.ticket,
                    s.name AS specialty_name,
                    s.room,
                    c.diagnosis
                FROM prescriptions pr
                JOIN appointments a ON a.id = pr.appointment_id
                JOIN patients p ON p.id = a.patient_id
                JOIN specialties s ON s.id = a.specialty_id
                JOIN consultations c ON c.id = pr.consultation_id
                ORDER BY pr.id DESC
                """
            ).fetchall()
            item_rows = conn.execute("SELECT * FROM prescription_items ORDER BY id").fetchall()
        items_by_prescription: Dict[int, List[Dict[str, Any]]] = {}
        for row in item_rows:
            items_by_prescription.setdefault(int(row["prescription_id"]), []).append(dict(row))
        prescriptions = []
        for row in rows:
            item = dict(row)
            item["items"] = items_by_prescription.get(int(row["id"]), [])
            prescriptions.append(item)
        return prescriptions

    def list_transactions(self) -> List[Dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT *
                FROM transactions
                ORDER BY id DESC
                """
            ).fetchall()
        return [dict(row) for row in rows]

    def stats(self) -> Dict[str, int]:
        appointments = self.list_appointments()
        prescriptions = self.list_prescriptions()
        return {
            "registered": len(appointments),
            "pending_payment": len([item for item in appointments if item["payment_status"] == "pending"]),
            "waiting_triage": len([item for item in appointments if item["triage_status"] in {"waiting", "in_progress"}]),
            "waiting_consultation": len([item for item in appointments if item["consultation_status"] == "waiting"]),
            "pending_pharmacy": len([item for item in prescriptions if item["status"] == "pending"]),
            "completed": len([item for item in appointments if item["status"] == "completed"]),
        }

    def get_setting(self, key: str) -> Optional[str]:
        with self._connect() as conn:
            row = conn.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
        return None if row is None else row["value"]

    def set_setting(self, key: str, value: Optional[str]) -> None:
        with self._connect() as conn:
            self._set_setting(conn, key, value)

    @staticmethod
    def _set_setting(conn: sqlite3.Connection, key: str, value: Optional[str]) -> None:
        if value is None:
            conn.execute("DELETE FROM settings WHERE key = ?", (key,))
        else:
            conn.execute(
                """
                INSERT INTO settings (key, value)
                VALUES (?, ?)
                ON CONFLICT(key) DO UPDATE SET value = excluded.value
                """,
                (key, value),
            )

    def authenticate_user(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT id, username, full_name, role, active 
                FROM users 
                WHERE username = ? AND password = ? AND active = 1
                """,
                (username, password),
            ).fetchone()
            return dict(row) if row else None

    def list_users(self) -> List[Dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute("SELECT id, username, full_name, role, active FROM users ORDER BY id").fetchall()
        return [dict(row) for row in rows]

    def list_patients(self) -> List[Dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute("SELECT * FROM patients WHERE active = 1 ORDER BY id DESC").fetchall()
        return [dict(row) for row in rows]

    def create_patient(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        data = _validate_patient_payload(payload)
        with self._connect() as conn:
            cursor = conn.execute(
                """
                INSERT INTO patients (
                    document, first_name, last_name, age, sex, birth_date, phone, active, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, 1, ?)
                """,
                (
                    data["document"],
                    data["first_name"],
                    data["last_name"],
                    data["age"],
                    data["sex"],
                    data["birth_date"],
                    data["phone"],
                    utc_now(),
                ),
            )
            patient_id = int(cursor.lastrowid)
        patient = self.get_patient(patient_id)
        if patient is None:
            raise RuntimeError("No se pudo recuperar el paciente.")
        return patient

    def get_patient(self, patient_id: int) -> Optional[Dict[str, Any]]:
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM patients WHERE id = ?", (patient_id,)).fetchone()
        return dict(row) if row else None

    def update_patient(self, patient_id: int, payload: Dict[str, Any]) -> Dict[str, Any]:
        current = self.get_patient(patient_id)
        if current is None:
            raise ValueError("Paciente no encontrado.")
        data = _validate_patient_payload({**current, **payload})
        with self._connect() as conn:
            conn.execute(
                """
                UPDATE patients
                SET document = ?, first_name = ?, last_name = ?, age = ?, sex = ?, birth_date = ?, phone = ?
                WHERE id = ?
                """,
                (
                    data["document"],
                    data["first_name"],
                    data["last_name"],
                    data["age"],
                    data["sex"],
                    data["birth_date"],
                    data["phone"],
                    patient_id,
                ),
            )
        patient = self.get_patient(patient_id)
        if patient is None:
            raise RuntimeError("No se pudo recuperar el paciente actualizado.")
        return patient

    def delete_patient(self, patient_id: int) -> None:
        with self._connect() as conn:
            conn.execute("UPDATE patients SET active = 0 WHERE id = ?", (patient_id,))

    def search_patients(self, query: str) -> List[Dict[str, Any]]:
        term = f"%{query.strip()}%"
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT * FROM patients
                WHERE active = 1
                  AND (document LIKE ? OR first_name LIKE ? OR last_name LIKE ?)
                ORDER BY id DESC
                LIMIT 25
                """,
                (term, term, term),
            ).fetchall()
        return [dict(row) for row in rows]

    def list_workers(self) -> List[Dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute("SELECT * FROM workers WHERE active = 1 ORDER BY id DESC").fetchall()
        return [dict(row) for row in rows]

    def get_worker(self, worker_id: int) -> Optional[Dict[str, Any]]:
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM workers WHERE id = ?", (worker_id,)).fetchone()
        return dict(row) if row else None

    def create_worker(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        data = _validate_worker_payload(payload)
        with self._connect() as conn:
            cursor = conn.execute(
                """
                INSERT INTO workers (
                    document, first_name, last_name, role, specialty, age, sex, birth_date, phone, active, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?)
                """,
                (
                    data["document"],
                    data["first_name"],
                    data["last_name"],
                    data["role"],
                    data["specialty"],
                    data["age"],
                    data["sex"],
                    data["birth_date"],
                    data["phone"],
                    utc_now(),
                ),
            )
            worker_id = int(cursor.lastrowid)
        worker = self.get_worker(worker_id)
        if worker is None:
            raise RuntimeError("No se pudo recuperar el trabajador.")
        return worker

    def update_worker(self, worker_id: int, payload: Dict[str, Any]) -> Dict[str, Any]:
        current = self.get_worker(worker_id)
        if current is None:
            raise ValueError("Trabajador no encontrado.")
        data = _validate_worker_payload({**current, **payload})
        with self._connect() as conn:
            conn.execute(
                """
                UPDATE workers
                SET document = ?, first_name = ?, last_name = ?, role = ?, specialty = ?,
                    age = ?, sex = ?, birth_date = ?, phone = ?
                WHERE id = ?
                """,
                (
                    data["document"],
                    data["first_name"],
                    data["last_name"],
                    data["role"],
                    data["specialty"],
                    data["age"],
                    data["sex"],
                    data["birth_date"],
                    data["phone"],
                    worker_id,
                ),
            )
        worker = self.get_worker(worker_id)
        if worker is None:
            raise RuntimeError("No se pudo recuperar el trabajador actualizado.")
        return worker

    def delete_worker(self, worker_id: int) -> None:
        with self._connect() as conn:
            conn.execute("UPDATE workers SET active = 0 WHERE id = ?", (worker_id,))

    def list_consultorios(self) -> List[Dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute("SELECT * FROM consultorios WHERE active = 1 ORDER BY name").fetchall()
        return [dict(row) for row in rows]

    def get_consultorio(self, consultorio_id: int) -> Optional[Dict[str, Any]]:
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM consultorios WHERE id = ?", (consultorio_id,)).fetchone()
        return dict(row) if row else None

    def create_consultorio(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        name = _required_text(payload.get("name"), "Nombre")
        floor = _required_text(payload.get("floor"), "Piso")
        equipment = _required_text(payload.get("equipment"), "Equipamiento")
        with self._connect() as conn:
            cursor = conn.execute(
                """
                INSERT INTO consultorios (name, floor, equipment, active, created_at)
                VALUES (?, ?, ?, 1, ?)
                """,
                (
                    name,
                    floor,
                    equipment,
                    utc_now(),
                ),
            )
            consultorio_id = int(cursor.lastrowid)
        consultorio = self.get_consultorio(consultorio_id)
        if consultorio is None:
            raise RuntimeError("No se pudo recuperar el consultorio.")
        return consultorio

    def update_consultorio(self, consultorio_id: int, payload: Dict[str, Any]) -> Dict[str, Any]:
        current = self.get_consultorio(consultorio_id)
        if current is None:
            raise ValueError("Consultorio no encontrado.")
        data = {**current, **payload}
        name = _required_text(data.get("name"), "Nombre")
        floor = _required_text(data.get("floor"), "Piso")
        equipment = _required_text(data.get("equipment"), "Equipamiento")
        with self._connect() as conn:
            conn.execute(
                """
                UPDATE consultorios
                SET name = ?, floor = ?, equipment = ?
                WHERE id = ?
                """,
                (
                    name,
                    floor,
                    equipment,
                    consultorio_id,
                ),
            )
        consultorio = self.get_consultorio(consultorio_id)
        if consultorio is None:
            raise RuntimeError("No se pudo recuperar el consultorio actualizado.")
        return consultorio

    def delete_consultorio(self, consultorio_id: int) -> None:
        with self._connect() as conn:
            conn.execute("UPDATE consultorios SET active = 0 WHERE id = ?", (consultorio_id,))

    def list_medications(self) -> List[Dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute("SELECT * FROM medications WHERE active = 1 ORDER BY name").fetchall()
        return [dict(row) for row in rows]

    def get_medication(self, medication_id: int) -> Optional[Dict[str, Any]]:
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM medications WHERE id = ?", (medication_id,)).fetchone()
        return dict(row) if row else None

    def create_medication(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        name = _required_text(payload.get("name"), "Nombre")
        description = _required_text(payload.get("description"), "Descripcion")
        price = float(payload.get("price") or 0)
        stock = int(payload.get("stock") or 0)
        if price < 0:
            raise ValueError("Precio no puede ser negativo.")
        if stock < 0:
            raise ValueError("Stock no puede ser negativo.")
        with self._connect() as conn:
            cursor = conn.execute(
                """
                INSERT INTO medications (name, description, price, stock, active, created_at)
                VALUES (?, ?, ?, ?, 1, ?)
                """,
                (
                    name,
                    description,
                    price,
                    stock,
                    utc_now(),
                ),
            )
            medication_id = int(cursor.lastrowid)
        medication = self.get_medication(medication_id)
        if medication is None:
            raise RuntimeError("No se pudo recuperar el medicamento.")
        return medication

    def update_medication(self, medication_id: int, payload: Dict[str, Any]) -> Dict[str, Any]:
        current = self.get_medication(medication_id)
        if current is None:
            raise ValueError("Medicamento no encontrado.")
        data = {**current, **payload}
        name = _required_text(data.get("name"), "Nombre")
        description = _required_text(data.get("description"), "Descripcion")
        price = float(data.get("price") or 0)
        stock = int(data.get("stock") or 0)
        if price < 0:
            raise ValueError("Precio no puede ser negativo.")
        if stock < 0:
            raise ValueError("Stock no puede ser negativo.")
        with self._connect() as conn:
            conn.execute(
                """
                UPDATE medications
                SET name = ?, description = ?, price = ?, stock = ?
                WHERE id = ?
                """,
                (
                    name,
                    description,
                    price,
                    stock,
                    medication_id,
                ),
            )
        medication = self.get_medication(medication_id)
        if medication is None:
            raise RuntimeError("No se pudo recuperar el medicamento actualizado.")
        return medication

    def delete_medication(self, medication_id: int) -> None:
        with self._connect() as conn:
            conn.execute("UPDATE medications SET active = 0 WHERE id = ?", (medication_id,))

    @staticmethod
    def _next_ticket(conn: sqlite3.Connection) -> str:
        count = conn.execute("SELECT COUNT(*) FROM appointments").fetchone()[0] + 1
        return f"A{count:04d}"

    @staticmethod
    def _next_transaction_code(conn: sqlite3.Connection, module: str) -> str:
        prefix = {"cashier": "CJ", "pharmacy": "FA"}.get(module, "TX")
        count = conn.execute(
            "SELECT COUNT(*) FROM transactions WHERE module = ?", (module,)
        ).fetchone()[0] + 1
        return f"{prefix}-{datetime.now().strftime('%Y%m%d%H%M%S')}-{count:04d}"

    def _record_transaction(
        self,
        conn: sqlite3.Connection,
        module: str,
        reference_type: str,
        reference_id: int,
        patient_document: str,
        patient_name: str,
        concept: str,
        amount: float,
        payment_method: str = "Efectivo",
        created_by: Optional[str] = None,
    ) -> Dict[str, Any]:
        existing = conn.execute(
            """
            SELECT *
            FROM transactions
            WHERE module = ? AND reference_type = ? AND reference_id = ? AND status = 'paid'
            LIMIT 1
            """,
            (module, reference_type, reference_id),
        ).fetchone()
        if existing:
            return dict(existing)

        conn.execute(
            """
            INSERT INTO transactions (
                transaction_code, module, reference_type, reference_id, patient_document,
                patient_name, concept, amount, payment_method, status, created_by, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'paid', ?, ?)
            """,
            (
                self._next_transaction_code(conn, module),
                module,
                reference_type,
                reference_id,
                patient_document,
                patient_name,
                concept,
                max(0.0, float(amount or 0)),
                _required_text(payment_method or "Efectivo", "Metodo de pago"),
                created_by or "",
                utc_now(),
            ),
        )
        row = conn.execute(
            "SELECT * FROM transactions WHERE id = last_insert_rowid()"
        ).fetchone()
        return dict(row) if row else {}

    @staticmethod
    def _audit(
        conn: sqlite3.Connection,
        event_type: str,
        entity: str,
        entity_id: Optional[int],
        message: str,
    ) -> None:
        conn.execute(
            """
            INSERT INTO audit_events (event_type, entity, entity_id, message, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (event_type, entity, entity_id, message, utc_now()),
        )

    @staticmethod
    def _appointment_dict(
        row: sqlite3.Row,
        triage: Optional[Dict[str, Any]],
        consultation: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        return {
            "id": row["id"],
            "ticket": row["ticket"],
            "status": row["status"],
            "payment_status": row["payment_status"],
            "triage_status": row["triage_status"],
            "consultation_status": row["consultation_status"],
            "pharmacy_status": row["pharmacy_status"],
            "room": row["room"],
            "scheduled_at": row["scheduled_at"],
            "receipt_code": row["receipt_code"],
            "created_at": row["created_at"],
            "paid_at": row["paid_at"],
            "patient": {
                "id": row["patient_id"],
                "document": row["patient_document"],
                "first_name": row["patient_first_name"],
                "last_name": row["patient_last_name"],
                "age": row["patient_age"],
                "sex": row["patient_sex"],
                "birth_date": row["patient_birth_date"],
                "phone": row["patient_phone"],
                "full_name": f"{row['patient_first_name']} {row['patient_last_name']}",
            },
            "specialty": {
                "id": row["specialty_id"],
                "name": row["specialty_name"],
                "price": row["specialty_price"],
                "duration_min": row["specialty_duration_min"],
                "doctor_name": row["specialty_doctor_name"],
            },
            "triage": triage,
            "consultation": consultation,
        }

    @staticmethod
    def _triage_dict(row: sqlite3.Row) -> Dict[str, Any]:
        data = dict(row)
        data["analysis"] = json.loads(data.get("analysis_json") or "{}")
        return data


class SupabaseRepository(BaseRepository):
    """REST adapter for Supabase. It expects supabase_schema.sql to be applied."""

    def __init__(self, url: str, key: str) -> None:
        self.url = url.rstrip("/")
        self.key = key

    def setup(self) -> None:
        if not self.list_specialties():
            for specialty in DEFAULT_SPECIALTIES:
                self._insert("specialties", specialty)

    def snapshot(self) -> Dict[str, Any]:
        appointments = self.list_appointments()
        prescriptions = self.list_prescriptions()
        return {
            "specialties": self.list_specialties(),
            "appointments": appointments,
            "prescriptions": prescriptions,
            "stats": self._stats(appointments, prescriptions),
            "active_triage_appointment_id": self.get_setting("active_triage_appointment_id"),
        }

    def list_specialties(self) -> List[Dict[str, Any]]:
        return self._select("specialties", {"select": "*", "order": "id.asc"})

    def get_appointment(self, appointment_id: int) -> Optional[Dict[str, Any]]:
        return next(
            (item for item in self.list_appointments() if int(item["id"]) == int(appointment_id)),
            None,
        )

    def list_appointments(self) -> List[Dict[str, Any]]:
        appointments = self._select("appointments", {"select": "*", "order": "id.desc"})
        patients = {item["id"]: item for item in self._select("patients", {"select": "*"})}
        specialties = {item["id"]: item for item in self.list_specialties()}
        triage = {
            item["appointment_id"]: self._triage_dict(item)
            for item in self._select("triage_records", {"select": "*"})
        }
        consultations = {
            item["appointment_id"]: item for item in self._select("consultations", {"select": "*"})
        }
        results = []
        for row in appointments:
            patient = patients.get(row["patient_id"], {})
            specialty = specialties.get(row["specialty_id"], {})
            results.append(
                {
                    **row,
                    "patient": {
                        **patient,
                        "full_name": f"{patient.get('first_name', '')} {patient.get('last_name', '')}".strip(),
                    },
                    "specialty": specialty,
                    "triage": triage.get(row["id"]),
                    "consultation": consultations.get(row["id"]),
                }
            )
        return results

    def create_patient_and_appointment(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        document = _validate_document(payload.get("document"))
        first_name = _required_text(payload.get("first_name"), "Nombres")
        last_name = _required_text(payload.get("last_name"), "Apellidos")
        age = _validate_age(payload.get("age"))
        sex = _required_text(payload.get("sex") or "No especificado", "Sexo")
        phone = _validate_phone(payload.get("phone"))
        specialty_id = int(payload.get("specialty_id") or 0)
        if specialty_id <= 0:
            raise ValueError("Faltan datos obligatorios del paciente o especialidad.")

        existing = self._select(
            "patients", {"select": "*", "document": f"eq.{document}", "limit": "1"}
        )
        patient_payload = {
            "document": document,
            "first_name": first_name,
            "last_name": last_name,
            "age": age,
            "sex": sex,
            "phone": phone,
        }
        if existing:
            patient = self._patch("patients", {"id": f"eq.{existing[0]['id']}"}, patient_payload)[0]
        else:
            patient = self._insert("patients", {**patient_payload, "created_at": utc_now()})[0]

        ticket = self._next_ticket()
        appointment = self._insert(
            "appointments",
            {
                "ticket": ticket,
                "patient_id": patient["id"],
                "specialty_id": specialty_id,
                "status": "registered",
                "payment_status": "pending",
                "triage_status": "not_started",
                "consultation_status": "not_started",
                "pharmacy_status": "none",
                "created_at": utc_now(),
            },
        )[0]
        self._audit("appointment_created", "appointments", appointment["id"], f"Cita {ticket} registrada")
        result = self.get_appointment(int(appointment["id"]))
        if result is None:
            raise RuntimeError("No se pudo recuperar la cita creada.")
        return result

    def mark_paid(self, appointment_id: int) -> Dict[str, Any]:
        appointment = self.get_appointment(appointment_id)
        if not appointment:
            raise ValueError("Cita no encontrada.")
        if appointment["payment_status"] == "paid":
            return appointment

        specialty = appointment["specialty"]
        paid_count = len(
            [
                item
                for item in self.list_appointments()
                if item["specialty_id"] == appointment["specialty_id"]
                and item["payment_status"] == "paid"
            ]
        )
        scheduled_at = local_now() + timedelta(minutes=(paid_count + 1) * int(specialty["duration_min"]))
        receipt_code = f"B{datetime.now().strftime('%Y%m%d%H%M')}-{appointment_id:04d}"
        self._patch(
            "appointments",
            {"id": f"eq.{appointment_id}"},
            {
                "status": "paid",
                "payment_status": "paid",
                "triage_status": "waiting",
                "consultation_status": "not_started",
                "pharmacy_status": "none",
                "room": specialty["room"],
                "scheduled_at": scheduled_at.isoformat(timespec="minutes"),
                "receipt_code": receipt_code,
                "paid_at": utc_now(),
            },
        )
        self._audit("payment_registered", "appointments", appointment_id, f"Pago {receipt_code} confirmado")
        return self.get_appointment(appointment_id) or appointment

    def set_active_triage(self, appointment_id: int) -> Dict[str, Any]:
        appointment = self.get_appointment(appointment_id)
        if not appointment:
            raise ValueError("Cita no encontrada.")
        if appointment["payment_status"] != "paid":
            raise ValueError("La cita debe estar pagada antes de triaje.")
        if appointment["triage_status"] == "done":
            raise ValueError("El triaje ya fue registrado.")
        self._patch(
            "appointments",
            {"id": f"eq.{appointment_id}"},
            {"status": "in_triage", "triage_status": "in_progress"},
        )
        self.set_setting("active_triage_appointment_id", str(appointment_id))
        self._audit("triage_started", "appointments", appointment_id, "Paciente activado para captura IoT")
        return self.get_appointment(appointment_id) or appointment

    def capture_triage(
        self,
        appointment_id: int,
        vitals: Dict[str, Any],
        analysis: Dict[str, Any],
        source: str,
    ) -> Dict[str, Any]:
        existing = self._select(
            "triage_records",
            {"select": "*", "appointment_id": f"eq.{appointment_id}", "limit": "1"},
        )
        payload = {
            "appointment_id": appointment_id,
            "temperature": float(vitals["temperature"]),
            "heart_rate": int(vitals["heart_rate"]),
            "spo2": int(vitals["spO2"]),
            "systolic": int(vitals["blood_pressure_systolic"]),
            "diastolic": int(vitals["blood_pressure_diastolic"]),
            "weight": float(vitals["weight"]),
            "height": float(vitals["height"]),
            "bmi": float(analysis["bmi"]),
            "priority": analysis["priority"],
            "risk_score": float(analysis["risk_probability"]),
            "risk_label": analysis["risk_label"],
            "predicted_systolic": float(analysis["predicted_systolic"]),
            "estimated_attention_minutes": float(analysis["estimated_attention_minutes"]),
            "decision_summary": analysis["decision_summary"],
            "analysis_json": json.dumps(analysis),
            "source": source,
            "captured_at": utc_now(),
        }
        if existing:
            self._patch("triage_records", {"id": f"eq.{existing[0]['id']}"}, payload)
        else:
            self._insert("triage_records", payload)
        self._patch(
            "appointments",
            {"id": f"eq.{appointment_id}"},
            {"status": "triaged", "triage_status": "done", "consultation_status": "waiting"},
        )
        if self.get_setting("active_triage_appointment_id") == str(appointment_id):
            self.set_setting("active_triage_appointment_id", None)
        self._audit("triage_captured", "triage_records", appointment_id, f"Triaje {analysis['priority']} registrado")
        return self.get_appointment(appointment_id) or {}

    def create_consultation(self, appointment_id: int, payload: Dict[str, Any]) -> Dict[str, Any]:
        appointment = self.get_appointment(appointment_id)
        if not appointment:
            raise ValueError("Cita no encontrada.")
        diagnosis = str(payload.get("diagnosis") or "").strip()
        if not diagnosis:
            raise ValueError("El diagnostico es obligatorio.")

        consultation_payload = {
            "appointment_id": appointment_id,
            "doctor_name": str(payload.get("doctor_name") or appointment["specialty"].get("doctor_name") or ""),
            "symptoms": str(payload.get("symptoms") or ""),
            "diagnosis": diagnosis,
            "treatment_notes": str(payload.get("treatment_notes") or ""),
            "notes": str(payload.get("notes") or ""),
        }
        existing = self._select(
            "consultations",
            {"select": "*", "appointment_id": f"eq.{appointment_id}", "limit": "1"},
        )
        if existing:
            consultation = self._patch(
                "consultations", {"id": f"eq.{existing[0]['id']}"}, consultation_payload
            )[0]
        else:
            consultation = self._insert(
                "consultations", {**consultation_payload, "created_at": utc_now()}
            )[0]

        old_pending = self._select(
            "prescriptions",
            {
                "select": "*",
                "appointment_id": f"eq.{appointment_id}",
                "status": "neq.dispensed",
            },
        )
        for item in old_pending:
            self._delete("prescriptions", {"id": f"eq.{item['id']}"})

        prescription_items = [
            item for item in payload.get("prescription_items") or [] if item.get("medicine")
        ]
        prescription_id = None
        if prescription_items:
            total = sum(
                max(1, int(item.get("quantity") or 1)) * max(0.0, float(item.get("unit_price") or 0))
                for item in prescription_items
            )
            prescription = self._insert(
                "prescriptions",
                {
                    "appointment_id": appointment_id,
                    "consultation_id": consultation["id"],
                    "status": "pending",
                    "total": total,
                    "created_at": utc_now(),
                },
            )[0]
            prescription_id = prescription["id"]
            for item in prescription_items:
                self._insert(
                    "prescription_items",
                    {
                        "prescription_id": prescription_id,
                        "medicine": str(item.get("medicine") or ""),
                        "dosage": str(item.get("dosage") or ""),
                        "frequency": str(item.get("frequency") or ""),
                        "days": max(1, int(item.get("days") or 1)),
                        "quantity": max(1, int(item.get("quantity") or 1)),
                        "unit_price": max(0.0, float(item.get("unit_price") or 0)),
                    },
                )

        self._patch(
            "appointments",
            {"id": f"eq.{appointment_id}"},
            {
                "status": "prescription_pending" if prescription_id else "completed",
                "consultation_status": "done",
                "pharmacy_status": "pending" if prescription_id else "none",
            },
        )
        self._audit("consultation_saved", "consultations", consultation["id"], "Consulta medica registrada")
        return self.get_appointment(appointment_id) or appointment

    def dispense_prescription(self, prescription_id: int) -> Dict[str, Any]:
        prescription = self._select(
            "prescriptions", {"select": "*", "id": f"eq.{prescription_id}", "limit": "1"}
        )
        if not prescription:
            raise ValueError("Receta no encontrada.")
        row = prescription[0]
        self._patch(
            "prescriptions",
            {"id": f"eq.{prescription_id}"},
            {"status": "dispensed", "dispensed_at": utc_now()},
        )
        self._patch(
            "appointments",
            {"id": f"eq.{row['appointment_id']}"},
            {"status": "completed", "pharmacy_status": "dispensed"},
        )
        self._audit("prescription_dispensed", "prescriptions", prescription_id, "Medicamentos entregados")
        return next(item for item in self.list_prescriptions() if int(item["id"]) == int(prescription_id))

    def list_prescriptions(self) -> List[Dict[str, Any]]:
        prescriptions = self._select("prescriptions", {"select": "*", "order": "id.desc"})
        items = self._select("prescription_items", {"select": "*", "order": "id.asc"})
        appointments = {item["id"]: item for item in self.list_appointments()}
        by_prescription: Dict[int, List[Dict[str, Any]]] = {}
        for item in items:
            by_prescription.setdefault(int(item["prescription_id"]), []).append(item)
        results = []
        for prescription in prescriptions:
            appointment = appointments.get(prescription["appointment_id"], {})
            patient = appointment.get("patient", {})
            specialty = appointment.get("specialty", {})
            row = {
                **prescription,
                "ticket": appointment.get("ticket"),
                "patient_name": patient.get("full_name"),
                "patient_document": patient.get("document"),
                "specialty_name": specialty.get("name"),
                "room": appointment.get("room"),
                "diagnosis": (appointment.get("consultation") or {}).get("diagnosis"),
                "items": by_prescription.get(int(prescription["id"]), []),
            }
            results.append(row)
        return results

    def get_setting(self, key: str) -> Optional[str]:
        rows = self._select("settings", {"select": "*", "key": f"eq.{key}", "limit": "1"})
        return rows[0]["value"] if rows else None

    def set_setting(self, key: str, value: Optional[str]) -> None:
        if value is None:
            self._delete("settings", {"key": f"eq.{key}"})
        elif self.get_setting(key) is None:
            self._insert("settings", {"key": key, "value": value})
        else:
            self._patch("settings", {"key": f"eq.{key}"}, {"value": value})

    def _request(
        self,
        method: str,
        table: str,
        params: Optional[Dict[str, str]] = None,
        payload: Optional[Any] = None,
        prefer: Optional[str] = None,
    ) -> Any:
        headers = {
            "apikey": self.key,
            "Authorization": f"Bearer {self.key}",
            "Content-Type": "application/json",
        }
        if prefer:
            headers["Prefer"] = prefer
        response = requests.request(
            method,
            f"{self.url}/rest/v1/{table}",
            params=params,
            json=payload,
            headers=headers,
            timeout=20,
        )
        if response.status_code >= 400:
            raise RuntimeError(f"Supabase {table}: {response.status_code} {response.text}")
        if response.text:
            return response.json()
        return []

    def _select(self, table: str, params: Optional[Dict[str, str]] = None) -> List[Dict[str, Any]]:
        return self._request("GET", table, params=params or {})

    def _insert(self, table: str, payload: Dict[str, Any]) -> List[Dict[str, Any]]:
        return self._request("POST", table, payload=payload, prefer="return=representation")

    def _patch(
        self, table: str, params: Dict[str, str], payload: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        return self._request("PATCH", table, params=params, payload=payload, prefer="return=representation")

    def _delete(self, table: str, params: Dict[str, str]) -> List[Dict[str, Any]]:
        return self._request("DELETE", table, params=params, prefer="return=representation")

    def _next_ticket(self) -> str:
        rows = self._select("appointments", {"select": "id", "order": "id.desc", "limit": "1"})
        next_id = int(rows[0]["id"]) + 1 if rows else 1
        return f"A{next_id:04d}"

    def _audit(self, event_type: str, entity: str, entity_id: Optional[int], message: str) -> None:
        self._insert(
            "audit_events",
            {
                "event_type": event_type,
                "entity": entity,
                "entity_id": entity_id,
                "message": message,
                "created_at": utc_now(),
            },
        )
    
        # ============== CRUD for Workers ==============
    def list_workers(self):
        conn = self._connect()
        rows = conn.execute('SELECT * FROM workers WHERE active = 1 ORDER BY id').fetchall()
        return [dict(row) for row in rows]

    def create_worker(self, payload):
        conn = self._connect()
        data = {
            'document': payload.get('document'),
            'first_name': payload.get('first_name'),
            'last_name': payload.get('last_name'),
            'role': payload.get('role'),
            'specialty': payload.get('specialty'),
            'phone': payload.get('phone'),
            'active': 1,
            'created_at': utc_now()
        }
        conn.execute('''INSERT INTO workers (document, first_name, last_name, role, specialty, phone, active, created_at)
            VALUES (:document, :first_name, :last_name, :role, :specialty, :phone, :active, :created_at)''', data)
        conn.commit()
        return self.get_worker(conn.lastrowid)

    def get_worker(self, worker_id):
        conn = self._connect()
        row = conn.execute('SELECT * FROM workers WHERE id = ?', (worker_id,)).fetchone()
        return dict(row) if row else None

    def update_worker(self, worker_id, payload):
        conn = self._connect()
        conn.execute('''UPDATE workers SET document=:document, first_name=:first_name, last_name=:last_name, 
            role=:role, specialty=:specialty, phone=:phone WHERE id=:id''', {**payload, 'id': worker_id})
        conn.commit()
        return self.get_worker(worker_id)

    def delete_worker(self, worker_id):
        conn = self._connect()
        conn.execute('UPDATE workers SET active = 0 WHERE id = ?', (worker_id,))
        conn.commit()

    # ============== CRUD for Consultorios ==============
    def list_consultorios(self):
        conn = self._connect()
        rows = conn.execute('SELECT * FROM consultorios WHERE active = 1 ORDER BY id').fetchall()
        return [dict(row) for row in rows]

    def create_consultorio(self, payload):
        conn = self._connect()
        data = {'name': payload.get('name'), 'floor': payload.get('floor'), 'equipment': payload.get('equipment'), 
               'active': 1, 'created_at': utc_now()}
        conn.execute('INSERT INTO consultorios (name, floor, equipment, active, created_at) VALUES (:name, :floor, :equipment, :active, :created_at)', data)
        conn.commit()
        return dict(conn.execute('SELECT * FROM consultorios WHERE id = ?', (conn.lastrowid,)).fetchone())

    def delete_consultorio(self, consultorio_id):
        conn = self._connect()
        conn.execute('UPDATE consultorios SET active = 0 WHERE id = ?', (consultorio_id,))
        conn.commit()

    # ============== CRUD for Medications ==============
    def list_medications(self):
        conn = self._connect()
        rows = conn.execute('SELECT * FROM medications WHERE active = 1 ORDER BY name').fetchall()
        return [dict(row) for row in rows]

    def create_medication(self, payload):
        conn = self._connect()
        data = {'name': payload.get('name'), 'description': payload.get('description'), 
               'price': payload.get('price', 0), 'stock': payload.get('stock', 0), 
               'active': 1, 'created_at': utc_now()}
        conn.execute('INSERT INTO medications (name, description, price, stock, active, created_at) VALUES (:name, :description, :price, :stock, :active, :created_at)', data)
        conn.commit()
        return dict(conn.execute('SELECT * FROM medications WHERE id = ?', (conn.lastrowid,)).fetchone())

    def update_medication(self, medication_id, payload):
        conn = self._connect()
        conn.execute('''UPDATE medications SET name=:name, description=:description, price=:price, stock=:stock WHERE id=:id''', 
            {**payload, 'id': medication_id})
        conn.commit()
        return dict(conn.execute('SELECT * FROM medications WHERE id = ?', (medication_id,)).fetchone())

    def delete_medication(self, medication_id):
        conn = self._connect()
        conn.execute('UPDATE medications SET active = 0 WHERE id = ?', (medication_id,))
        conn.commit()

    # ============== Search Patients ==============
    def search_patients(self, query):
        conn = self._connect()
        rows = conn.execute('''SELECT * FROM patients WHERE document LIKE ? OR first_name LIKE ? OR last_name LIKE ? LIMIT 20''',
            (f'%{query}%', f'%{query}%', f'%{query}%')).fetchall()
        return [dict(row) for row in rows]
    
    def get_patient(self, patient_id):
        conn = self._connect()
        row = conn.execute('SELECT * FROM patients WHERE id = ?', (patient_id,)).fetchone()
        return dict(row) if row else None

    def update_patient(self, patient_id, payload):
        conn = self._connect()
        conn.execute("UPDATE patients SET document=:document, first_name=:first_name, last_name=:last_name, age=:age, sex=:sex, phone=:phone WHERE id=:id", 
            {**payload, 'id': patient_id})
        conn.commit()
        return self.get_patient(patient_id)

    def delete_patient(self, patient_id):
        conn = self._connect()
        conn.execute('DELETE FROM patients WHERE id = ?', (patient_id,))
        conn.commit()



    @staticmethod
    def _stats(appointments: Sequence[Dict[str, Any]], prescriptions: Sequence[Dict[str, Any]]) -> Dict[str, int]:
        return {
            "registered": len(appointments),
            "pending_payment": len([item for item in appointments if item["payment_status"] == "pending"]),
            "waiting_triage": len([item for item in appointments if item["triage_status"] in {"waiting", "in_progress"}]),
            "waiting_consultation": len([item for item in appointments if item["consultation_status"] == "waiting"]),
            "pending_pharmacy": len([item for item in prescriptions if item["status"] == "pending"]),
            "completed": len([item for item in appointments if item["status"] == "completed"]),
        }

    @staticmethod
    def _triage_dict(row: Dict[str, Any]) -> Dict[str, Any]:
        return {**row, "analysis": json.loads(row.get("analysis_json") or "{}")}

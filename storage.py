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
        "nombre": "Medicina General",
        "precio": 55.0,
        "duracion_minutos": 20,
        "consultorio": "C-101",
        "nombre_medico": "Dra. Valeria Ramos",
    },
    {
        "id": 2,
        "nombre": "Pediatria",
        "precio": 70.0,
        "duracion_minutos": 20,
        "consultorio": "C-102",
        "nombre_medico": "Dr. Mateo Aguilar",
    },
    {
        "id": 3,
        "nombre": "Cardiologia",
        "precio": 120.0,
        "duracion_minutos": 30,
        "consultorio": "C-201",
        "nombre_medico": "Dra. Camila Torres",
    },
    {
        "id": 4,
        "nombre": "Dermatologia",
        "precio": 90.0,
        "duracion_minutos": 20,
        "consultorio": "C-202",
        "nombre_medico": "Dr. Alonso Vega",
    },
    {
        "id": 5,
        "nombre": "Ginecologia",
        "precio": 100.0,
        "duracion_minutos": 25,
        "consultorio": "C-203",
        "nombre_medico": "Dra. Sofia Paredes",
    },
    {
        "id": 6,
        "nombre": "Traumatologia",
        "precio": 110.0,
        "duracion_minutos": 25,
        "consultorio": "C-204",
        "nombre_medico": "Dr. Diego Salazar",
    },
]
DEFAULT_USERS = [
    {"id": 1, "nombre_usuario": "admin", "contrasena": "admin123", "nombre_completo": "Administrador", "rol": "admin"},
    {"id": 2, "nombre_usuario": "recep", "contrasena": "recep123", "nombre_completo": "Maria Lopez", "rol": "reception"},
    {"id": 3, "nombre_usuario": "caja", "contrasena": "caja123", "nombre_completo": "Carlos Perez", "rol": "cashier"},
    {"id": 4, "nombre_usuario": "triedad", "contrasena": "triedad123", "nombre_completo": "Ana Torres", "rol": "triedad"},
    {"id": 5, "nombre_usuario": "doctor", "contrasena": "doctor123", "nombre_completo": "Dr. Roberto Silva", "rol": "doctor"},
    {"id": 6, "nombre_usuario": "farmacia", "contrasena": "farm123", "nombre_completo": "Laura Gomez", "rol": "pharmacy"},
]
def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def local_now() -> datetime:
    return datetime.now()


def _clean_digits(valor: Any) -> str:
    return "".join(char for char in str(valor or "").strip() if char.isdigit())


def _validate_documento(valor: Any, label: str = "DNI") -> str:
    documento = _clean_digits(valor)
    if len(documento) != 8:
        raise ValueError(f"{label} debe tener 8 digitos.")
    return documento


def _validate_telefono(valor: Any) -> str:
    telefono = _clean_digits(valor)
    if len(telefono) != 9:
        raise ValueError("Telefono debe tener 9 digitos y no aceptar letras.")
    return telefono


def _required_text(valor: Any, label: str) -> str:
    text = str(valor or "").strip()
    if not text:
        raise ValueError(f"{label} es obligatorio.")
    return text


def _validate_edad(valor: Any) -> int:
    edad = int(valor or 0)
    if edad < 1 or edad > 120:
        raise ValueError("Edad debe estar entre 1 y 120.")
    return edad


def _optional_edad(valor: Any) -> Optional[int]:
    if valor in (None, ""):
        return None
    return _validate_edad(valor)


def _optional_date_text(valor: Any) -> str:
    return str(valor or "").strip()[:10]


def _validate_patient_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "documento": _validate_documento(payload.get("documento")),
        "nombre": _required_text(payload.get("nombre"), "Nombres"),
        "apellido": _required_text(payload.get("apellido"), "Apellidos"),
        "edad": _validate_edad(payload.get("edad")),
        "sexo": _required_text(payload.get("sexo") or "No especificado", "Sexo"),
        "telefono": _validate_telefono(payload.get("telefono")),
        "fecha_nacimiento": _optional_date_text(payload.get("fecha_nacimiento")),
    }


def _validate_worker_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    rol = _required_text(payload.get("rol"), "Rol")
    specialty = str(payload.get("specialty") or "").strip()
    if rol == "doctor" and not specialty:
        raise ValueError("Especialidad es obligatoria para trabajadores medicos.")
    return {
        "documento": _validate_documento(payload.get("documento")),
        "nombre": _required_text(payload.get("nombre"), "Nombres"),
        "apellido": _required_text(payload.get("apellido"), "Apellidos"),
        "rol": rol,
        "specialty": specialty if rol == "doctor" else "",
        "telefono": _validate_telefono(payload.get("telefono")),
        "edad": _optional_edad(payload.get("edad")),
        "sexo": _required_text(payload.get("sexo") or "No especificado", "Sexo"),
        "fecha_nacimiento": _optional_date_text(payload.get("fecha_nacimiento")),
    }


def create_repository() -> "BaseRepository":
    storedad_mode = os.getenv("APP_STORAGE", "sqlite").lower()
    if storedad_mode == "supabase":
        return SupabaseRepository(
            url=os.environ["SUPABASE_URL"],
            clave=os.environ["SUPABASE_SERVICE_ROLE_KEY"],
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

    def list_especialidades(self) -> List[Dict[str, Any]]:
        raise NotImplementedError

    def get_appointment(self, id_cita: int) -> Optional[Dict[str, Any]]:
        raise NotImplementedError

    def create_patient_and_appointment(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        raise NotImplementedError

    def mark_paid(
        self,
        id_cita: int,
        metodo_pago: str = "Efectivo",
        creado_por: Optional[str] = None,
    ) -> Dict[str, Any]:
        raise NotImplementedError

    def set_activo_triedad(self, id_cita: int) -> Dict[str, Any]:
        raise NotImplementedError

    def capture_triedad(
        self,
        id_cita: int,
        vitals: Dict[str, Any],
        analysis: Dict[str, Any],
        fuente: str,
    ) -> Dict[str, Any]:
        raise NotImplementedError

    def create_consultation(self, id_cita: int, payload: Dict[str, Any]) -> Dict[str, Any]:
        raise NotImplementedError

    def dispense_prescription(
        self,
        id_receta: int,
        metodo_pago: str = "Efectivo",
        creado_por: Optional[str] = None,
        payment_method: Optional[str] = None,
        created_by: Optional[str] = None,
    ) -> Dict[str, Any]:
        raise NotImplementedError

    def list_transacciones(self) -> List[Dict[str, Any]]:
        raise NotImplementedError

    def get_setting(self, clave: str) -> Optional[str]:
        raise NotImplementedError

    def set_setting(self, clave: str, valor: Optional[str]) -> None:
        raise NotImplementedError

    def authenticate_user(self, nombre_usuario: str, contrasena: str) -> Optional[Dict[str, Any]]:
        raise NotImplementedError

    def list_usuarios(self) -> List[Dict[str, Any]]:
        raise NotImplementedError


class SQLiteRepository(BaseRepository):
    def __init__(self, db_path: str) -> None:
        self.db_path = Path(db_path)

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_claves = ON")
        return connection

    def setup(self) -> None:
        with self._connect() as conn:
            conn.executescript(
                """
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
                    fecha_creacion TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS especialidades (
                    id INTEGER PRIMARY KEY,
                    nombre TEXT NOT NULL,
                    precio REAL NOT NULL,
                    duracion_minutos INTEGER NOT NULL,
                    consultorio TEXT NOT NULL,
                    nombre_medico TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS citas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ticket TEXT NOT NULL UNIQUE,
                    id_paciente INTEGER NOT NULL REFERENCES pacientes(id),
                    id_especialidad INTEGER NOT NULL REFERENCES especialidades(id),
                    estado TEXT NOT NULL,
                    estado_pago TEXT NOT NULL,
                    estado_triaje TEXT NOT NULL,
                    estado_consulta TEXT NOT NULL,
                    estado_farmacia TEXT NOT NULL,
                    consultorio TEXT,
                    fecha_programada TEXT,
                    codigo_recibo TEXT,
                    fecha_creacion TEXT NOT NULL,
                    fecha_pago TEXT
                );

                CREATE TABLE IF NOT EXISTS expedientes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    id_cita INTEGER NOT NULL UNIQUE REFERENCES citas(id),
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
                    fecha_captura TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS consultas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    id_cita INTEGER NOT NULL UNIQUE REFERENCES citas(id),
                    nombre_medico TEXT NOT NULL,
                    sintomas TEXT NOT NULL,
                    diagnostico TEXT NOT NULL,
                    tratamiento TEXT NOT NULL,
                    notas TEXT,
                    fecha_creacion TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS recetas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    id_cita INTEGER NOT NULL REFERENCES citas(id),
                    id_consulta INTEGER NOT NULL REFERENCES consultas(id),
                    estado TEXT NOT NULL,
                    total REAL NOT NULL,
                    fecha_creacion TEXT NOT NULL,
                    fecha_dispensacion TEXT
                );

                CREATE TABLE IF NOT EXISTS receta_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    id_receta INTEGER NOT NULL REFERENCES recetas(id) ON DELETE CASCADE,
                    medicamento TEXT NOT NULL,
                    dosis TEXT NOT NULL,
                    frecuencia TEXT NOT NULL,
                    dias INTEGER NOT NULL,
                    cantidad INTEGER NOT NULL,
                    unit_precio REAL NOT NULL
                );

                CREATE TABLE IF NOT EXISTS transacciones (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    codigo_transaccion TEXT NOT NULL UNIQUE,
                    modulo TEXT NOT NULL,
                    tipo_referencia TEXT NOT NULL,
                    id_referencia INTEGER NOT NULL,
                    documento_paciente TEXT NOT NULL,
                    nombre_paciente TEXT NOT NULL,
                    concepto TEXT NOT NULL,
                    monto REAL NOT NULL,
                    metodo_pago TEXT NOT NULL,
                    estado TEXT NOT NULL,
                    creado_por TEXT,
                    fecha_creacion TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS usuarios (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nombre_usuario TEXT NOT NULL UNIQUE,
                    contrasena TEXT NOT NULL,
                    nombre_completo TEXT NOT NULL,
                    rol TEXT NOT NULL,
                    activo INTEGER NOT NULL DEFAULT 1,
                    fecha_creacion TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS configuracion (
                    clave TEXT PRIMARY KEY,
                    valor TEXT
                );

                CREATE TABLE IF NOT EXISTS eventos_auditoria (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tipo_evento TEXT NOT NULL,
                    entidad TEXT NOT NULL,
                    entidad_id INTEGER,
                    mensaje TEXT NOT NULL,
                    fecha_creacion TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS trabajadores (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    documento TEXT NOT NULL UNIQUE,
                    nombre TEXT NOT NULL,
                    apellido TEXT NOT NULL,
                    rol TEXT NOT NULL,
                    specialty TEXT,
                    edad INTEGER,
                    sexo TEXT DEFAULT 'No especificado',
                    fecha_nacimiento TEXT,
                    telefono TEXT,
                    activo INTEGER DEFAULT 1,
                    fecha_creacion TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS consultorios (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nombre TEXT NOT NULL,
                    floor TEXT,
                    equipment TEXT,
                    activo INTEGER DEFAULT 1,
                    fecha_creacion TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS medicamentos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nombre TEXT NOT NULL,
                    description TEXT,
                    precio REAL DEFAULT 0,
                    stock INTEGER DEFAULT 0,
                    activo INTEGER DEFAULT 1,
                    fecha_creacion TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS trabajadores (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    documento TEXT NOT NULL UNIQUE,
                    nombre TEXT NOT NULL,
                    apellido TEXT NOT NULL,
                    rol TEXT NOT NULL,
                    specialty TEXT,
                    telefono TEXT,
                    activo INTEGER DEFAULT 1,
                    fecha_creacion TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS consultorios (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nombre TEXT NOT NULL,
                    floor TEXT,
                    equipment TEXT,
                    activo INTEGER DEFAULT 1,
                    fecha_creacion TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS medicamentos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nombre TEXT NOT NULL,
                    description TEXT,
                    precio REAL DEFAULT 0,
                    stock INTEGER DEFAULT 0,
                    activo INTEGER DEFAULT 1,
                    fecha_creacion TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS trabajadores (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    documento TEXT NOT NULL UNIQUE,
                    nombre TEXT NOT NULL,
                    apellido TEXT NOT NULL,
                    rol TEXT NOT NULL,
                    specialty TEXT,
                    telefono TEXT,
                    activo INTEGER DEFAULT 1,
                    fecha_creacion TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS consultorios (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nombre TEXT NOT NULL,
                    floor TEXT,
                    equipment TEXT,
                    activo INTEGER DEFAULT 1,
                    fecha_creacion TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS medicamentos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nombre TEXT NOT NULL,
                    description TEXT,
                    precio REAL DEFAULT 0,
                    stock INTEGER DEFAULT 0,
                    activo INTEGER DEFAULT 1,
                    fecha_creacion TEXT NOT NULL
                );

                """
            )
            patient_columns = {
                row[1] for row in conn.execute("PRAGMA table_info(pacientes)").fetchall()
            }
            if "activo" not in patient_columns:
                conn.execute("ALTER TABLE pacientes ADD COLUMN activo INTEGER NOT NULL DEFAULT 1")
            if "fecha_nacimiento" not in patient_columns:
                conn.execute("ALTER TABLE pacientes ADD COLUMN fecha_nacimiento TEXT")

            worker_columns = {
                row[1] for row in conn.execute("PRAGMA table_info(trabajadores)").fetchall()
            }
            if "edad" not in worker_columns:
                conn.execute("ALTER TABLE trabajadores ADD COLUMN edad INTEGER")
            if "sexo" not in worker_columns:
                conn.execute("ALTER TABLE trabajadores ADD COLUMN sexo TEXT DEFAULT 'No especificado'")
            if "fecha_nacimiento" not in worker_columns:
                conn.execute("ALTER TABLE trabajadores ADD COLUMN fecha_nacimiento TEXT")
            existing = conn.execute("SELECT COUNT(*) FROM especialidades").fetchone()[0]
            if existing == 0:
                conn.executemany(
                    """
                    INSERT INTO especialidades (id, nombre, precio, duracion_minutos, consultorio, nombre_medico)
                    VALUES (:id, :nombre, :precio, :duracion_minutos, :consultorio, :nombre_medico)
                    """,
                    DEFAULT_SPECIALTIES,
                )
            existing_user = conn.execute("SELECT COUNT(*) FROM usuarios").fetchone()[0]
            if existing_user == 0:
                conn.executemany(
                    """
                    INSERT INTO usuarios (id, nombre_usuario, contrasena, nombre_completo, rol, activo, fecha_creacion)
                    VALUES (:id, :nombre_usuario, :contrasena, :nombre_completo, :rol, :activo, :fecha_creacion)
                    """,
                    [
                        {"id": 1, "nombre_usuario": "admin", "contrasena": "admin123", "nombre_completo": "Administrador", "rol": "admin", "activo": 1, "fecha_creacion": utc_now()},
                        {"id": 2, "nombre_usuario": "recep", "contrasena": "recep123", "nombre_completo": "Maria Lopez", "rol": "reception", "activo": 1, "fecha_creacion": utc_now()},
                        {"id": 3, "nombre_usuario": "caja", "contrasena": "caja123", "nombre_completo": "Carlos Perez", "rol": "cashier", "activo": 1, "fecha_creacion": utc_now()},
                        {"id": 4, "nombre_usuario": "triedad", "contrasena": "triedad123", "nombre_completo": "Ana Torres", "rol": "triedad", "activo": 1, "fecha_creacion": utc_now()},
                        {"id": 5, "nombre_usuario": "doctor", "contrasena": "doctor123", "nombre_completo": "Dr. Roberto Silva", "rol": "doctor", "activo": 1, "fecha_creacion": utc_now()},
                        {"id": 6, "nombre_usuario": "farmacia", "contrasena": "farm123", "nombre_completo": "Laura Gomez", "rol": "pharmacy", "activo": 1, "fecha_creacion": utc_now()},
                    ],
                )
            if conn.execute("SELECT COUNT(*) FROM trabajadores").fetchone()[0] == 0:
                conn.executemany(
                    """
                    INSERT INTO trabajadores (documento, nombre, apellido, rol, specialty, telefono, activo, fecha_creacion)
                    VALUES (:documento, :nombre, :apellido, :rol, :specialty, :telefono, 1, :fecha_creacion)
                    """,
                    [
                        {"documento": "44556677", "nombre": "Valeria", "apellido": "Ramos", "rol": "doctor", "specialty": "Medicina General", "telefono": "987654321", "fecha_creacion": utc_now()},
                        {"documento": "45678912", "nombre": "Mateo", "apellido": "Aguilar", "rol": "doctor", "specialty": "Pediatria", "telefono": "987111222", "fecha_creacion": utc_now()},
                        {"documento": "47889900", "nombre": "Ana", "apellido": "Torres", "rol": "triedad", "specialty": "Enfermeria", "telefono": "986222333", "fecha_creacion": utc_now()},
                        {"documento": "48990011", "nombre": "Maria", "apellido": "Lopez", "rol": "reception", "specialty": "", "telefono": "985333444", "fecha_creacion": utc_now()},
                        {"documento": "49001122", "nombre": "Carlos", "apellido": "Perez", "rol": "cashier", "specialty": "", "telefono": "984444555", "fecha_creacion": utc_now()},
                        {"documento": "50112233", "nombre": "Laura", "apellido": "Gomez", "rol": "pharmacy", "specialty": "Farmacia", "telefono": "983555666", "fecha_creacion": utc_now()},
                    ],
                )
            if conn.execute("SELECT COUNT(*) FROM consultorios").fetchone()[0] == 0:
                conn.executemany(
                    """
                    INSERT INTO consultorios (nombre, floor, equipment, activo, fecha_creacion)
                    VALUES (:nombre, :floor, :equipment, 1, :fecha_creacion)
                    """,
                    [
                        {"nombre": "C-101", "floor": "Piso 1", "equipment": "Camilla, tensiometro, PC", "fecha_creacion": utc_now()},
                        {"nombre": "C-102", "floor": "Piso 1", "equipment": "Pediatria, balanza pediatrica", "fecha_creacion": utc_now()},
                        {"nombre": "C-201", "floor": "Piso 2", "equipment": "ECG, monitor cardiaco", "fecha_creacion": utc_now()},
                        {"nombre": "Triedad 01", "floor": "Piso 1", "equipment": "IoT signos vitales, oximetro", "fecha_creacion": utc_now()},
                    ],
                )
            if conn.execute("SELECT COUNT(*) FROM medicamentos").fetchone()[0] == 0:
                conn.executemany(
                    """
                    INSERT INTO medicamentos (nombre, description, precio, stock, activo, fecha_creacion)
                    VALUES (:nombre, :description, :precio, :stock, 1, :fecha_creacion)
                    """,
                    [
                        {"nombre": "Paracetamol 500 mg", "description": "Analgesico y antipiretico", "precio": 1.50, "stock": 120, "fecha_creacion": utc_now()},
                        {"nombre": "Ibuprofeno 400 mg", "description": "Antiinflamatorio", "precio": 2.20, "stock": 80, "fecha_creacion": utc_now()},
                        {"nombre": "Amoxicilina 500 mg", "description": "Antibiotico", "precio": 3.80, "stock": 60, "fecha_creacion": utc_now()},
                        {"nombre": "Loratadina 10 mg", "description": "Antihistaminico", "precio": 1.80, "stock": 90, "fecha_creacion": utc_now()},
                        {"nombre": "Suero oral", "description": "Rehidratacion oral", "precio": 4.50, "stock": 45, "fecha_creacion": utc_now()},
                    ],
                )
            if conn.execute("SELECT COUNT(*) FROM pacientes").fetchone()[0] == 0:
                conn.executemany(
                    """
                    INSERT INTO pacientes (documento, nombre, apellido, edad, sexo, telefono, activo, fecha_creacion)
                    VALUES (:documento, :nombre, :apellido, :edad, :sexo, :telefono, 1, :fecha_creacion)
                    """,
                    [
                        {"documento": "70123456", "nombre": "Lucia", "apellido": "Herrera", "edad": 28, "sexo": "Femenino", "telefono": "999111222", "fecha_creacion": utc_now()},
                        {"documento": "70456789", "nombre": "Jorge", "apellido": "Salinas", "edad": 46, "sexo": "Masculino", "telefono": "999333444", "fecha_creacion": utc_now()},
                        {"documento": "70890123", "nombre": "Elena", "apellido": "Quispe", "edad": 67, "sexo": "Femenino", "telefono": "999555666", "fecha_creacion": utc_now()},
                    ],
                )
                rows = conn.execute("SELECT id FROM pacientes ORDER BY id").fetchall()
                demo_citas = [
                    ("A0001", rows[0]["id"], 1, "registered", "pending", "not_started", "not_started", "none"),
                    ("A0002", rows[1]["id"], 3, "paid", "paid", "waiting", "not_started", "none"),
                    ("A0003", rows[2]["id"], 1, "triedadd", "paid", "done", "waiting", "none"),
                ]
                conn.executemany(
                    """
                    INSERT INTO citas (
                        ticket, id_paciente, id_especialidad, estado, estado_pago, estado_triaje,
                        estado_consulta, estado_farmacia, consultorio, fecha_programada, codigo_recibo, fecha_creacion, fecha_pago
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'C-101', ?, 'B-DEMO', ?, ?)
                    """,
                    [
                        (
                            ticket,
                            id_paciente,
                            id_especialidad,
                            estado,
                            estado_pago,
                            estado_triaje,
                            estado_consulta,
                            estado_farmacia,
                            local_now().isoformat(timespec="minutes"),
                            utc_now(),
                            utc_now() if estado_pago == "paid" else None,
                        )
                        for ticket, id_paciente, id_especialidad, estado, estado_pago, estado_triaje, estado_consulta, estado_farmacia in demo_citas
                    ],
                )
            self._seed_demo_data(conn)

    def _seed_demo_data(self, conn: sqlite3.Connection) -> None:
        especialidades = {
            row["id"]: dict(row)
            for row in conn.execute("SELECT * FROM especialidades").fetchall()
        }

        def ensure_patient(payload: Dict[str, Any]) -> int:
            existing = conn.execute(
                "SELECT id FROM pacientes WHERE documento = ?", (payload["documento"],)
            ).fetchone()
            if existing:
                conn.execute(
                    """
                    UPDATE pacientes
                    SET nombre = COALESCE(NULLIF(nombre, ''), :nombre),
                        apellido = COALESCE(NULLIF(apellido, ''), :apellido),
                        edad = COALESCE(edad, :edad),
                        sexo = COALESCE(NULLIF(sexo, ''), :sexo),
                        fecha_nacimiento = COALESCE(NULLIF(fecha_nacimiento, ''), :fecha_nacimiento),
                        telefono = COALESCE(NULLIF(telefono, ''), :telefono),
                        activo = 1
                    WHERE id = :id
                    """,
                    {**payload, "id": existing["id"]},
                )
                return int(existing["id"])

            cursor = conn.execute(
                """
                INSERT INTO pacientes (
                    documento, nombre, apellido, edad, sexo, fecha_nacimiento, telefono, activo, fecha_creacion
                )
                VALUES (:documento, :nombre, :apellido, :edad, :sexo, :fecha_nacimiento, :telefono, 1, :fecha_creacion)
                """,
                {**payload, "fecha_creacion": utc_now()},
            )
            return int(cursor.lastrowid)

        demo_pacientes = {
            "Rosa": ensure_patient(
                {
                    "documento": "70987654",
                    "nombre": "Rosa",
                    "apellido": "Medina Torres",
                    "edad": 34,
                    "sexo": "Femenino",
                    "fecha_nacimiento": "1992-04-13",
                    "telefono": "997123456",
                }
            ),
            "Miguel": ensure_patient(
                {
                    "documento": "71345678",
                    "nombre": "Miguel",
                    "apellido": "Castro Leon",
                    "edad": 52,
                    "sexo": "Masculino",
                    "fecha_nacimiento": "1974-02-09",
                    "telefono": "996234567",
                }
            ),
            "Carmen": ensure_patient(
                {
                    "documento": "72456789",
                    "nombre": "Carmen",
                    "apellido": "Flores Rivas",
                    "edad": 71,
                    "sexo": "Femenino",
                    "fecha_nacimiento": "1955-11-21",
                    "telefono": "995345678",
                }
            ),
            "Diego": ensure_patient(
                {
                    "documento": "73567890",
                    "nombre": "Diego",
                    "apellido": "Rojas Vega",
                    "edad": 39,
                    "sexo": "Masculino",
                    "fecha_nacimiento": "1987-07-02",
                    "telefono": "994456789",
                }
            ),
            "Patricia": ensure_patient(
                {
                    "documento": "74678901",
                    "nombre": "Patricia",
                    "apellido": "Nunez Soto",
                    "edad": 29,
                    "sexo": "Femenino",
                    "fecha_nacimiento": "1997-09-18",
                    "telefono": "993567890",
                }
            ),
        }

        def ensure_appointment(
            ticket: str,
            id_paciente: int,
            id_especialidad: int,
            estado: str,
            estado_pago: str,
            estado_triaje: str,
            estado_consulta: str,
            estado_farmacia: str,
            minutes_ahead: int,
        ) -> int:
            existing = conn.execute(
                "SELECT id FROM citas WHERE ticket = ?", (ticket,)
            ).fetchone()
            if existing:
                return int(existing["id"])

            specialty = especialidades[id_especialidad]
            paid = estado_pago == "paid"
            cursor = conn.execute(
                """
                INSERT INTO citas (
                    ticket, id_paciente, id_especialidad, estado, estado_pago, estado_triaje,
                    estado_consulta, estado_farmacia, consultorio, fecha_programada, codigo_recibo, fecha_creacion, fecha_pago
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    ticket,
                    id_paciente,
                    id_especialidad,
                    estado,
                    estado_pago,
                    estado_triaje,
                    estado_consulta,
                    estado_farmacia,
                    specialty["consultorio"] if paid else None,
                    (local_now() + timedelta(minutes=minutes_ahead)).isoformat(timespec="minutes")
                    if paid
                    else None,
                    f"B-DEMO-{ticket}" if paid else None,
                    utc_now(),
                    utc_now() if paid else None,
                ),
            )
            return int(cursor.lastrowid)

        citas = {
            "A0101": ensure_appointment(
                "A0101", demo_pacientes["Rosa"], 1, "registered", "pending",
                "not_started", "not_started", "none", 0
            ),
            "A0102": ensure_appointment(
                "A0102", demo_pacientes["Miguel"], 3, "paid", "paid",
                "waiting", "not_started", "none", 20
            ),
            "A0103": ensure_appointment(
                "A0103", demo_pacientes["Carmen"], 1, "triedadd", "paid",
                "done", "waiting", "none", 35
            ),
            "A0104": ensure_appointment(
                "A0104", demo_pacientes["Diego"], 4, "prescription_pending", "paid",
                "done", "done", "pending", 50
            ),
            "A0105": ensure_appointment(
                "A0105", demo_pacientes["Patricia"], 2, "completed", "paid",
                "done", "done", "dispensed", 65
            ),
        }

        def ensure_triedad(id_cita: int, vitals: Dict[str, Any], analysis: Dict[str, Any]) -> None:
            existing = conn.execute(
                "SELECT id FROM expedientes WHERE id_cita = ?", (id_cita,)
            ).fetchone()
            if existing:
                return
            conn.execute(
                """
                INSERT INTO expedientes (
                    id_cita, temperatura, ritmo_cardiaco, spo2, sistolica, diastolica,
                    peso, altura, imc, prioridad, puntuacion_riesgo, etiqueta_riesgo,
                    sistolica_predicha, minutos_estimados, resumen_decision,
                    analisis_json, fuente, fecha_captura
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'Demo IoT', ?)
                """,
                (
                    id_cita,
                    vitals["temperatura"],
                    vitals["ritmo_cardiaco"],
                    vitals["spo2"],
                    vitals["sistolica"],
                    vitals["diastolica"],
                    vitals["peso"],
                    vitals["altura"],
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
        ensure_triedad(
            citas["A0103"],
            {
                "temperatura": 38.4,
                "ritmo_cardiaco": 112,
                "spo2": 94,
                "sistolica": 146,
                "diastolica": 88,
                "peso": 73.0,
                "altura": 154.0,
            },
            {
                "imc": 30.78,
                "risk_probability": 0.68,
                "etiqueta_riesgo": "Moderado",
                "prioridad": "Urgente",
                "sistolica_predicha": 139.4,
                "minutos_estimados": 24.0,
                "flags": ["Fiebre", "Frecuencia cardiaca alta", "Saturacion baja"],
                "resumen_decision": "Urgente por fiebre, frecuencia cardiaca alta y saturacion baja. Riesgo moderado.",
                "algorithms": base_algorithms,
            },
        )
        ensure_triedad(
            citas["A0104"],
            {
                "temperatura": 37.1,
                "ritmo_cardiaco": 86,
                "spo2": 97,
                "sistolica": 126,
                "diastolica": 79,
                "peso": 84.0,
                "altura": 172.0,
            },
            {
                "imc": 28.39,
                "risk_probability": 0.24,
                "etiqueta_riesgo": "Bajo",
                "prioridad": "Rutina",
                "sistolica_predicha": 127.1,
                "minutos_estimados": 15.5,
                "flags": [],
                "resumen_decision": "Rutina. Signos dentro de rango operativo. Riesgo bajo.",
                "algorithms": base_algorithms,
            },
        )
        ensure_triedad(
            citas["A0105"],
            {
                "temperatura": 36.8,
                "ritmo_cardiaco": 92,
                "spo2": 98,
                "sistolica": 120,
                "diastolica": 76,
                "peso": 62.0,
                "altura": 161.0,
            },
            {
                "imc": 23.92,
                "risk_probability": 0.18,
                "etiqueta_riesgo": "Bajo",
                "prioridad": "Rutina",
                "sistolica_predicha": 129.6,
                "minutos_estimados": 14.0,
                "flags": [],
                "resumen_decision": "Rutina. Signos dentro de rango operativo. Riesgo bajo.",
                "algorithms": base_algorithms,
            },
        )

        def ensure_consultation(
            id_cita: int,
            nombre_medico: str,
            sintomas: str,
            diagnostico: str,
            tratamiento_notas: str,
        ) -> int:
            existing = conn.execute(
                "SELECT id FROM consultas WHERE id_cita = ?", (id_cita,)
            ).fetchone()
            if existing:
                return int(existing["id"])
            cursor = conn.execute(
                """
                INSERT INTO consultas (
                    id_cita, nombre_medico, sintomas, diagnostico, tratamiento_notas, notas, fecha_creacion
                )
                VALUES (?, ?, ?, ?, ?, '', ?)
                """,
                (id_cita, nombre_medico, sintomas, diagnostico, tratamiento_notas, utc_now()),
            )
            return int(cursor.lastrowid)

        consultation_a0104 = ensure_consultation(
            citas["A0104"],
            "Dr. Alonso Vega",
            "Lesiones pruriginosas en antebrazo desde hace 3 dias.",
            "Dermatitis alergica leve",
            "Evitar irritantes, antihistaminico y control si progresa.",
        )
        consultation_a0105 = ensure_consultation(
            citas["A0105"],
            "Dr. Mateo Aguilar",
            "Dolor de garganta y fiebre referida.",
            "Faringitis aguda",
            "Reposo, hidratacion y analgesico segun dolor.",
        )

        def ensure_prescription(
            id_cita: int,
            id_consulta: int,
            estado: str,
            dispensed: bool,
            items: Sequence[Dict[str, Any]],
        ) -> int:
            existing = conn.execute(
                "SELECT id FROM recetas WHERE id_cita = ?", (id_cita,)
            ).fetchone()
            if existing:
                return int(existing["id"])
            total = sum(float(item["unit_precio"]) * int(item["cantidad"]) for item in items)
            cursor = conn.execute(
                """
                INSERT INTO recetas (
                    id_cita, id_consulta, estado, total, fecha_creacion, fecha_dispensacion
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    id_cita,
                    id_consulta,
                    estado,
                    total,
                    utc_now(),
                    utc_now() if dispensed else None,
                ),
            )
            id_receta = int(cursor.lastrowid)
            conn.executemany(
                """
                INSERT INTO receta_items (
                    id_receta, medicamento, dosis, frecuencia, dias, cantidad, unit_precio
                )
                VALUES (:id_receta, :medicamento, :dosis, :frecuencia, :dias, :cantidad, :unit_precio)
                """,
                [dict(item, id_receta=id_receta) for item in items],
            )
            return id_receta

        prescription_a0104 = ensure_prescription(
            citas["A0104"],
            consultation_a0104,
            "pending",
            False,
            [
                {
                    "medicamento": "Loratadina 10 mg",
                    "dosis": "1 tableta",
                    "frecuencia": "Cada 24 horas",
                    "dias": 5,
                    "cantidad": 5,
                    "unit_precio": 1.80,
                },
                {
                    "medicamento": "Paracetamol 500 mg",
                    "dosis": "1 tableta",
                    "frecuencia": "Si hay dolor",
                    "dias": 3,
                    "cantidad": 6,
                    "unit_precio": 1.50,
                },
            ],
        )
        prescription_a0105 = ensure_prescription(
            citas["A0105"],
            consultation_a0105,
            "dispensed",
            True,
            [
                {
                    "medicamento": "Paracetamol 500 mg",
                    "dosis": "1 tableta",
                    "frecuencia": "Cada 8 horas",
                    "dias": 3,
                    "cantidad": 9,
                    "unit_precio": 1.50,
                },
                {
                    "medicamento": "Suero oral",
                    "dosis": "1 sobre",
                    "frecuencia": "Segun tolerancia",
                    "dias": 2,
                    "cantidad": 2,
                    "unit_precio": 4.50,
                },
            ],
        )

        self._backfill_transacciones(conn)
        prescription = conn.execute(
            """
            SELECT pr.*, a.ticket, p.documento AS documento_paciente,
                   p.nombre || ' ' || p.apellido AS nombre_paciente
            FROM recetas pr
            JOIN citas a ON a.id = pr.id_cita
            JOIN pacientes p ON p.id = a.id_paciente
            WHERE pr.id = ?
            """,
            (prescription_a0105,),
        ).fetchone()
        if prescription:
            self._record_transaction(
                conn,
                modulo="pharmacy",
                tipo_referencia="prescription",
                id_referencia=prescription_a0105,
                documento_paciente=prescription["documento_paciente"],
                nombre_paciente=prescription["nombre_paciente"],
                concepto=f"Medicamentos - {prescription['ticket']}",
                monto=float(prescription["total"] or 0),
                metodo_pago="Yape",
                creado_por="farmacia",
            )

    def _backfill_transacciones(self, conn: sqlite3.Connection) -> None:
        paid_citas = conn.execute(
            """
            SELECT a.id, p.documento AS documento_paciente,
                   p.nombre || ' ' || p.apellido AS nombre_paciente,
                   s.nombre AS especialidad_nombre, s.precio AS specialty_precio
            FROM citas a
            JOIN pacientes p ON p.id = a.id_paciente
            JOIN especialidades s ON s.id = a.id_especialidad
            WHERE a.estado_pago = 'paid'
            """
        ).fetchall()
        for row in paid_citas:
            self._record_transaction(
                conn,
                modulo="cashier",
                tipo_referencia="appointment",
                id_referencia=int(row["id"]),
                documento_paciente=row["documento_paciente"],
                nombre_paciente=row["nombre_paciente"],
                concepto=f"Consulta - {row['especialidad_nombre']}",
                monto=float(row["specialty_precio"] or 0),
                metodo_pago="Efectivo",
                creado_por="seed",
            )

        dispensed_recetas = conn.execute(
            """
            SELECT pr.id, pr.total, a.ticket, p.documento AS documento_paciente,
                   p.nombre || ' ' || p.apellido AS nombre_paciente
            FROM recetas pr
            JOIN citas a ON a.id = pr.id_cita
            JOIN pacientes p ON p.id = a.id_paciente
            WHERE pr.estado = 'dispensed'
            """
        ).fetchall()
        for row in dispensed_recetas:
            self._record_transaction(
                conn,
                modulo="pharmacy",
                tipo_referencia="prescription",
                id_referencia=int(row["id"]),
                documento_paciente=row["documento_paciente"],
                nombre_paciente=row["nombre_paciente"],
                concepto=f"Medicamentos - {row['ticket']}",
                monto=float(row["total"] or 0),
                metodo_pago="Efectivo",
                creado_por="seed",
            )
    def snapshot(self) -> Dict[str, Any]:
        with self._connect() as conn:
            paciente_rows = conn.execute("SELECT * FROM pacientes ORDER BY id").fetchall()
            especialidad_rows = conn.execute("SELECT * FROM especialidades ORDER BY id").fetchall()
            cita_rows = conn.execute("SELECT * FROM citas ORDER BY id").fetchall()
            expediente_rows = conn.execute("SELECT * FROM expedientes ORDER BY id").fetchall()
            consulta_rows = conn.execute("SELECT * FROM consultas ORDER BY id").fetchall()
            receta_rows = conn.execute("SELECT * FROM recetas ORDER BY id").fetchall()
            receta_item_rows = conn.execute("SELECT * FROM receta_items ORDER BY id").fetchall()
            transaccion_rows = conn.execute("SELECT * FROM transacciones ORDER BY id").fetchall()
            usuario_rows = conn.execute("SELECT * FROM usuarios ORDER BY id").fetchall()
            trabajador_rows = conn.execute("SELECT * FROM trabajadores ORDER BY id").fetchall()
            medicamento_rows = conn.execute("SELECT * FROM medicamentos ORDER BY id").fetchall()
            consultorio_rows = conn.execute("SELECT * FROM consultorios ORDER BY id").fetchall()
        return {
            "pacientes": [dict(row) for row in paciente_rows],
            "especialidades": [dict(row) for row in especialidad_rows],
            "citas": [dict(row) for row in cita_rows],
            "expedientes": [dict(row) for row in expediente_rows],
            "consultas": [dict(row) for row in consulta_rows],
            "recetas": [dict(row) for row in receta_rows],
            "receta_items": [dict(row) for row in receta_item_rows],
            "transacciones": [dict(row) for row in transaccion_rows],
            "usuarios": [dict(row) for row in usuario_rows],
            "trabajadores": [dict(row) for row in trabajador_rows],
            "medicamentos": [dict(row) for row in medicamento_rows],
            "consultorios": [dict(row) for row in consultorio_rows],
            "stats": self.stats(),
            "activo_triedad_id_cita": self.get_setting("activo_triedad_id_cita"),
            "called_triedad_id_cita": self.get_setting("called_triedad_id_cita"),
            "called_doctor_id_cita": self.get_setting("called_doctor_id_cita"),
        }

    def list_especialidades(self) -> List[Dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute("SELECT * FROM especialidades ORDER BY id").fetchall()
        return [dict(row) for row in rows]

    def list_citas(self) -> List[Dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT
                    a.*,
                    p.documento AS documento_paciente,
                    p.nombre AS patient_nombre,
                    p.apellido AS patient_apellido,
                    p.edad AS patient_edad,
                    p.sexo AS patient_sexo,
                    p.fecha_nacimiento AS patient_fecha_nacimiento,
                    p.telefono AS patient_telefono,
                    s.nombre AS especialidad_nombre,
                    s.precio AS specialty_precio,
                    s.duracion_minutos AS specialty_duracion_min,
                    s.nombre_medico AS especialidad_nombre_medico
                FROM citas a
                JOIN pacientes p ON p.id = a.id_paciente
                JOIN especialidades s ON s.id = a.id_especialidad
                ORDER BY a.id DESC
                """
            ).fetchall()
            triedad_rows = conn.execute("SELECT * FROM expedientes").fetchall()
            consultation_rows = conn.execute("SELECT * FROM consultas").fetchall()
        triedad_by_appointment = {row["id_cita"]: self._triedad_dict(row) for row in triedad_rows}
        consultation_by_appointment = {
            row["id_cita"]: dict(row) for row in consultation_rows
        }
        return [
            self._appointment_dict(
                row,
                triedad_by_appointment.get(row["id"]),
                consultation_by_appointment.get(row["id"]),
            )
            for row in rows
        ]

    def get_appointment(self, id_cita: int) -> Optional[Dict[str, Any]]:
        return next(
            (item for item in self.list_citas() if int(item["id"]) == int(id_cita)),
            None,
        )

    def create_patient_and_appointment(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        patient_data = _validate_patient_payload(payload)
        id_especialidad = int(payload.get("id_especialidad") or 0)

        if id_especialidad <= 0:
            raise ValueError("Faltan datos obligatorios del paciente o especialidad.")

        with self._connect() as conn:
            patient = conn.execute(
                "SELECT id FROM pacientes WHERE documento = ?", (patient_data["documento"],)
            ).fetchone()
            if patient:
                id_paciente = int(patient["id"])
                conn.execute(
                    """
                    UPDATE pacientes
                    SET nombre = ?, apellido = ?, edad = ?, sexo = ?, fecha_nacimiento = ?, telefono = ?
                    WHERE id = ?
                    """,
                    (
                        patient_data["nombre"],
                        patient_data["apellido"],
                        patient_data["edad"],
                        patient_data["sexo"],
                        patient_data["fecha_nacimiento"],
                        patient_data["telefono"],
                        id_paciente,
                    ),
                )
            else:
                cursor = conn.execute(
                    """
                    INSERT INTO pacientes (
                        documento, nombre, apellido, edad, sexo, fecha_nacimiento, telefono, activo, fecha_creacion
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, 1, ?)
                    """,
                    (
                        patient_data["documento"],
                        patient_data["nombre"],
                        patient_data["apellido"],
                        patient_data["edad"],
                        patient_data["sexo"],
                        patient_data["fecha_nacimiento"],
                        patient_data["telefono"],
                        utc_now(),
                    ),
                )
                id_paciente = int(cursor.lastrowid)

            ticket = self._next_ticket(conn)
            cursor = conn.execute(
                """
                INSERT INTO citas (
                    ticket, id_paciente, id_especialidad, estado, estado_pago, estado_triaje,
                    estado_consulta, estado_farmacia, fecha_creacion
                )
                VALUES (?, ?, ?, 'registered', 'pending', 'not_started', 'not_started', 'none', ?)
                """,
                (ticket, id_paciente, id_especialidad, utc_now()),
            )
            id_cita = int(cursor.lastrowid)
            self._audit(conn, "appointment_created", "citas", id_cita, f"Cita {ticket} registrada")
        appointment = self.get_appointment(id_cita)
        if appointment is None:
            raise RuntimeError("No se pudo recuperar la cita creada.")
        return appointment

    def mark_paid(
        self,
        id_cita: int,
        metodo_pago: str = "Efectivo",
        creado_por: Optional[str] = None,
    ) -> Dict[str, Any]:
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT
                    a.*,
                    p.documento AS documento_paciente,
                    p.nombre || ' ' || p.apellido AS nombre_paciente,
                    s.nombre AS especialidad_nombre,
                    s.precio AS specialty_precio,
                    s.consultorio,
                    s.duracion_minutos
                FROM citas a
                JOIN pacientes p ON p.id = a.id_paciente
                JOIN especialidades s ON s.id = a.id_especialidad
                WHERE a.id = ?
                """,
                (id_cita,),
            ).fetchone()
            if row is None:
                raise ValueError("Cita no encontrada.")
            if row["estado_pago"] == "paid":
                self._record_transaction(
                    conn,
                    modulo="cashier",
                    tipo_referencia="appointment",
                    id_referencia=id_cita,
                    documento_paciente=row["documento_paciente"],
                    nombre_paciente=row["nombre_paciente"],
                    concepto=f"Consulta - {row['especialidad_nombre']}",
                    monto=float(row["specialty_precio"] or 0),
                    metodo_pago=metodo_pago,
                    creado_por=creado_por,
                )
            else:
                paid_count = conn.execute(
                    """
                    SELECT COUNT(*) FROM citas
                    WHERE id_especialidad = ? AND estado_pago = 'paid'
                    """,
                    (row["id_especialidad"],),
                ).fetchone()[0]
                fecha_programada = local_now() + timedelta(minutes=(paid_count + 1) * int(row["duracion_minutos"]))
                codigo_recibo = f"B{datetime.now().strftime('%Y%m%d%H%M')}-{id_cita:04d}"
                conn.execute(
                    """
                    UPDATE citas
                    SET estado = 'paid',
                        estado_pago = 'paid',
                        estado_triaje = 'waiting',
                        estado_consulta = 'not_started',
                        estado_farmacia = 'none',
                        consultorio = ?,
                        fecha_programada = ?,
                        codigo_recibo = ?,
                        fecha_pago = ?
                    WHERE id = ?
                    """,
                    (
                        row["consultorio"],
                        fecha_programada.isoformat(timespec="minutes"),
                        codigo_recibo,
                        utc_now(),
                        id_cita,
                    ),
                )
                self._audit(conn, "payment_registered", "citas", id_cita, f"Pago {codigo_recibo} confirmado")
                self._record_transaction(
                    conn,
                    modulo="cashier",
                    tipo_referencia="appointment",
                    id_referencia=id_cita,
                    documento_paciente=row["documento_paciente"],
                    nombre_paciente=row["nombre_paciente"],
                    concepto=f"Consulta - {row['especialidad_nombre']}",
                    monto=float(row["specialty_precio"] or 0),
                    metodo_pago=metodo_pago,
                    creado_por=creado_por,
                )
        appointment = self.get_appointment(id_cita)
        if appointment is None:
            raise RuntimeError("No se pudo recuperar la cita pagada.")
        return appointment

    def set_activo_triedad(self, id_cita: int) -> Dict[str, Any]:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM citas WHERE id = ?", (id_cita,)
            ).fetchone()
            if row is None:
                raise ValueError("Cita no encontrada.")
            if row["estado_pago"] not in ("paid", "pagado"):
                raise ValueError("La cita debe estar pagada antes de triaje.")
            if row["estado_triaje"] in ("done", "finalizado"):
                raise ValueError("El triaje ya fue registrado.")

            conn.execute(
                """
                UPDATE citas
                SET estado = 'in_triedad', estado_triaje = 'in_progress'
                WHERE id = ?
                """,
                (id_cita,),
            )
            self._set_setting(conn, "activo_triedad_id_cita", str(id_cita))
            self._audit(conn, "triedad_started", "citas", id_cita, "Paciente activado para captura IoT")
        appointment = self.get_appointment(id_cita)
        if appointment is None:
            raise RuntimeError("No se pudo recuperar la cita activa.")
        return appointment

    def capture_triedad(
        self,
        id_cita: int,
        vitals: Dict[str, Any],
        analysis: Dict[str, Any],
        fuente: str,
    ) -> Dict[str, Any]:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM citas WHERE id = ?", (id_cita,)
            ).fetchone()
            if row is None:
                raise ValueError("Cita no encontrada.")
            fecha_captura = utc_now()
            conn.execute(
                """
                INSERT INTO expedientes (
                    id_cita, temperatura, ritmo_cardiaco, spo2, sistolica, diastolica,
                    peso, altura, imc, prioridad, puntuacion_riesgo, etiqueta_riesgo,
                    sistolica_predicha, minutos_estimados, resumen_decision,
                    analisis_json, fuente, fecha_captura
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id_cita) DO UPDATE SET
                    temperatura = excluded.temperatura,
                    ritmo_cardiaco = excluded.ritmo_cardiaco,
                    spo2 = excluded.spo2,
                    sistolica = excluded.sistolica,
                    diastolica = excluded.diastolica,
                    peso = excluded.peso,
                    altura = excluded.altura,
                    imc = excluded.imc,
                    prioridad = excluded.prioridad,
                    puntuacion_riesgo = excluded.puntuacion_riesgo,
                    etiqueta_riesgo = excluded.etiqueta_riesgo,
                    sistolica_predicha = excluded.sistolica_predicha,
                    minutos_estimados = excluded.minutos_estimados,
                    resumen_decision = excluded.resumen_decision,
                    analisis_json = excluded.analisis_json,
                    fuente = excluded.fuente,
                    fecha_captura = excluded.fecha_captura
                """,
                (
                    id_cita,
                    float(vitals["temperatura"]),
                    int(vitals["ritmo_cardiaco"]),
                    int(vitals["spO2"]),
                    int(vitals["blood_pressure_sistolica"]),
                    int(vitals["blood_pressure_diastolica"]),
                    float(vitals["peso"]),
                    float(vitals["altura"]),
                    float(analysis["bmi"]),
                    analysis["priority"],
                    float(analysis["risk_probability"]),
                    analysis["risk_label"],
                    float(analysis["predicted_systolic"]),
                    float(analysis["estimated_attention_minutes"]),
                    analysis["decision_summary"],
                    json.dumps(analysis),
                    fuente,
                    fecha_captura,
                ),
            )
            next_estado = "triedadd"
            conn.execute(
                """
                UPDATE citas
                SET estado = ?,
                    estado_triaje = 'done',
                    estado_consulta = 'waiting'
                WHERE id = ?
                """,
                (next_estado, id_cita),
            )
            activo = conn.execute(
                "SELECT valor FROM configuracion WHERE clave = 'activo_triedad_id_cita'"
            ).fetchone()
            if activo and activo["valor"] == str(id_cita):
                self._set_setting(conn, "activo_triedad_id_cita", None)
            self._audit(conn, "triedad_captured", "expedientes", id_cita, f"Triaje {analysis['priority']} registrado")
        appointment = self.get_appointment(id_cita)
        if appointment is None:
            raise RuntimeError("No se pudo recuperar la cita con triaje.")
        return appointment

    def create_consultation(self, id_cita: int, payload: Dict[str, Any]) -> Dict[str, Any]:
        sintomas = str(payload.get("sintomas") or "").strip()
        diagnostico = str(payload.get("diagnostico") or "").strip()
        tratamiento = str(payload.get("tratamiento") or "").strip()
        notas = str(payload.get("notas") or "").strip()
        nombre_medico = str(payload.get("nombre_medico") or "").strip()
        items = [item for item in payload.get("receta_items") or [] if item.get("medicamento")]

        if not diagnostico:
            raise ValueError("El diagnostico es obligatorio.")

        with self._connect() as conn:
            appointment = conn.execute(
                """
                SELECT a.*, s.nombre_medico
                FROM citas a
                JOIN especialidades s ON s.id = a.id_especialidad
                WHERE a.id = ?
                """,
                (id_cita,),
            ).fetchone()
            if appointment is None:
                raise ValueError("Cita no encontrada.")
            nombre_medico = nombre_medico or appointment["nombre_medico"]

            existing = conn.execute(
                "SELECT id FROM consultas WHERE id_cita = ?", (id_cita,)
            ).fetchone()
            if existing:
                id_consulta = int(existing["id"])
                conn.execute(
                    """
                    UPDATE consultas
                    SET nombre_medico = ?, sintomas = ?, diagnostico = ?, tratamiento = ?, notas = ?
                    WHERE id = ?
                    """,
                    (nombre_medico, sintomas, diagnostico, tratamiento, notas, id_consulta),
                )
            else:
                cursor = conn.execute(
                    """
                    INSERT INTO consultas (
                        id_cita, nombre_medico, sintomas, diagnostico, tratamiento, notas, fecha_creacion
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (id_cita, nombre_medico, sintomas, diagnostico, tratamiento, notas, utc_now()),
                )
                id_consulta = int(cursor.lastrowid)

            old_recetas = conn.execute(
                "SELECT id, estado FROM recetas WHERE id_cita = ?", (id_cita,)
            ).fetchall()
            for old in old_recetas:
                if old["estado"] not in ("dispensed", "dispensado"):
                    conn.execute("DELETE FROM recetas WHERE id = ?", (old["id"],))

            total = 0.0
            id_receta: Optional[int] = None
            if items:
                normalized_items = []
                for item in items:
                    cantidad = max(1, int(item.get("cantidad") or 1))
                    unit_precio = max(0.0, float(item.get("unit_precio") or 0))
                    dias = max(1, int(item.get("dias") or 1))
                    normalized_items.append(
                        {
                            "medicamento": str(item.get("medicamento") or "").strip(),
                            "dosis": str(item.get("dosis") or "").strip(),
                            "frecuencia": str(item.get("frecuencia") or "").strip(),
                            "dias": dias,
                            "cantidad": cantidad,
                            "unit_precio": unit_precio,
                        }
                    )
                    total += cantidad * unit_precio

                cursor = conn.execute(
                    """
                    INSERT INTO recetas (id_cita, id_consulta, estado, total, fecha_creacion)
                    VALUES (?, ?, 'pending', ?, ?)
                    """,
                    (id_cita, id_consulta, total, utc_now()),
                )
                id_receta = int(cursor.lastrowid)
                conn.executemany(
                    """
                    INSERT INTO receta_items (
                        id_receta, medicamento, dosis, frecuencia, dias, cantidad, unit_precio
                    )
                    VALUES (:id_receta, :medicamento, :dosis, :frecuencia, :dias, :cantidad, :unit_precio)
                    """,
                    [dict(item, id_receta=id_receta) for item in normalized_items],
                )

            estado_farmacia = "pending" if id_receta else "none"
            estado = "prescription_pending" if id_receta else "completed"
            conn.execute(
                """
                UPDATE citas
                SET estado = ?,
                    estado_consulta = 'done',
                    estado_farmacia = ?
                WHERE id = ?
                """,
                (estado, estado_farmacia, id_cita),
            )
            self._audit(conn, "consultation_saved", "consultas", id_consulta, "Consulta medica registrada")
        appointment_data = self.get_appointment(id_cita)
        if appointment_data is None:
            raise RuntimeError("No se pudo recuperar la consulta.")
        return appointment_data

    def dispense_prescription(
        self,
        id_receta: int,
        metodo_pago: str = "Efectivo",
        creado_por: Optional[str] = None,
        payment_method: Optional[str] = None,
        created_by: Optional[str] = None,
    ) -> Dict[str, Any]:
        with self._connect() as conn:
            prescription = conn.execute(
                """
                SELECT
                    pr.*,
                    a.ticket,
                    p.documento AS documento_paciente,
                    p.nombre || ' ' || p.apellido AS nombre_paciente
                FROM recetas pr
                JOIN citas a ON a.id = pr.id_cita
                JOIN pacientes p ON p.id = a.id_paciente
                WHERE pr.id = ?
                """,
                (id_receta,),
            ).fetchone()
            if prescription is None:
                raise ValueError("Receta no encontrada.")
            items = conn.execute(
                "SELECT medicina, cantidad FROM receta_items WHERE id_receta = ?",
                (id_receta,),
            ).fetchall()
            conn.execute(
                """
                UPDATE recetas
                SET estado = 'dispensed', fecha_dispensacion = ?
                WHERE id = ?
                """,
                (utc_now(), id_receta),
            )
            conn.execute(
                """
                UPDATE citas
                SET estado = 'completed', estado_farmacia = 'dispensed'
                WHERE id = ?
                """,
                (prescription["id_cita"],),
            )
            for item in items:
                conn.execute(
                    """
                    UPDATE medicamentos
                    SET stock = CASE WHEN stock >= ? THEN stock - ? ELSE 0 END
                    WHERE lower(nombre) = lower(?) AND activo = 1
                    """,
                    (int(item["cantidad"]), int(item["cantidad"]), item["medicina"]),
                )
            self._record_transaction(
                conn,
                modulo="pharmacy",
                tipo_referencia="prescription",
                id_referencia=id_receta,
                documento_paciente=prescription["documento_paciente"],
                nombre_paciente=prescription["nombre_paciente"],
                concepto=f"Medicamentos - {prescription['ticket']}",
                monto=float(prescription["total"] or 0),
                metodo_pago=metodo_pago,
                creado_por=creado_por,
            )
            self._audit(conn, "prescription_dispensed", "recetas", id_receta, "Medicamentos entregados")
        return self.list_prescription(id_receta)

    def list_prescription(self, id_receta: int) -> Dict[str, Any]:
        return next(
            item for item in self.list_recetas() if int(item["id"]) == int(id_receta)
        )

    def list_recetas(self) -> List[Dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT
                    pr.*,
                    p.nombre || ' ' || p.apellido AS nombre_paciente,
                    p.documento AS documento_paciente,
                    a.ticket,
                    s.nombre AS especialidad_nombre,
                    s.consultorio,
                    c.diagnostico
                FROM recetas pr
                JOIN citas a ON a.id = pr.id_cita
                JOIN pacientes p ON p.id = a.id_paciente
                JOIN especialidades s ON s.id = a.id_especialidad
                JOIN consultas c ON c.id = pr.id_consulta
                ORDER BY pr.id ASC
                """
            ).fetchall()
            item_rows = conn.execute("SELECT * FROM receta_items ORDER BY id").fetchall()
        items_by_prescription: Dict[int, List[Dict[str, Any]]] = {}
        for row in item_rows:
            items_by_prescription.setdefault(int(row["id_receta"]), []).append(dict(row))
        recetas = []
        for row in rows:
            item = dict(row)
            item["items"] = items_by_prescription.get(int(row["id"]), [])
            # Map estado -> status para compatibilidad con frontend
            # Map estado -> status para frontend: pending/dispensed
            raw = item.get("estado", "")
            if raw == "pendiente" or raw == "pending":
                item["status"] = "pending"
            elif raw == "dispensado" or raw == "dispensed":
                item["status"] = "dispensed"
            else:
                item["status"] = raw or ""
            recetas.append(item)
        return recetas

    def list_transacciones(self) -> List[Dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT *
                FROM transacciones
                ORDER BY id DESC
                """
            ).fetchall()
        return [dict(row) for row in rows]

    def stats(self) -> Dict[str, int]:
        citas = self.list_citas()
        recetas = self.list_recetas()
        return {
            "registered": len(citas),
            "pending_payment": len([item for item in citas if item["estado_pago"] == "pending"]),
            "waiting_triedad": len([item for item in citas if item["estado_triaje"] in {"waiting", "in_progress"}]),
            "waiting_consultation": len([item for item in citas if item["estado_consulta"] == "waiting"]),
            "pending_pharmacy": len([item for item in recetas if item.get("status") == "pending"]),
            "completed": len([item for item in citas if item["estado"] == "completed"]),
        }

    def get_setting(self, clave: str) -> Optional[str]:
        with self._connect() as conn:
            row = conn.execute("SELECT valor FROM configuracion WHERE clave = ?", (clave,)).fetchone()
        return None if row is None else row["valor"]

    def set_setting(self, clave: str, valor: Optional[str]) -> None:
        with self._connect() as conn:
            self._set_setting(conn, clave, valor)

    @staticmethod
    def _set_setting(conn: sqlite3.Connection, clave: str, valor: Optional[str]) -> None:
        if valor is None:
            conn.execute("DELETE FROM configuracion WHERE clave = ?", (clave,))
        else:
            conn.execute(
                """
                INSERT INTO configuracion (clave, valor)
                VALUES (?, ?)
                ON CONFLICT(clave) DO UPDATE SET valor = excluded.valor
                """,
                (clave, valor),
            )

    def authenticate_user(self, nombre_usuario: str, contrasena: str) -> Optional[Dict[str, Any]]:
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT id, nombre_usuario, nombre_completo, rol, activo 
                FROM usuarios 
                WHERE nombre_usuario = ? AND contrasena = ? AND activo = 1
                """,
                (nombre_usuario, contrasena),
            ).fetchone()
            return dict(row) if row else None

    def list_usuarios(self) -> List[Dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute("SELECT id, nombre_usuario, nombre_completo, rol, activo FROM usuarios ORDER BY id").fetchall()
        return [dict(row) for row in rows]

    def list_pacientes(self) -> List[Dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute("SELECT * FROM pacientes WHERE activo = 1 ORDER BY id DESC").fetchall()
        return [dict(row) for row in rows]

    def create_patient(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        data = _validate_patient_payload(payload)
        with self._connect() as conn:
            cursor = conn.execute(
                """
                INSERT INTO pacientes (
                    documento, nombre, apellido, edad, sexo, fecha_nacimiento, telefono, activo, fecha_creacion
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, 1, ?)
                """,
                (
                    data["documento"],
                    data["nombre"],
                    data["apellido"],
                    data["edad"],
                    data["sexo"],
                    data["fecha_nacimiento"],
                    data["telefono"],
                    utc_now(),
                ),
            )
            id_paciente = int(cursor.lastrowid)
        patient = self.get_patient(id_paciente)
        if patient is None:
            raise RuntimeError("No se pudo recuperar el paciente.")
        return patient

    def get_patient(self, id_paciente: int) -> Optional[Dict[str, Any]]:
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM pacientes WHERE id = ?", (id_paciente,)).fetchone()
        return dict(row) if row else None

    def update_patient(self, id_paciente: int, payload: Dict[str, Any]) -> Dict[str, Any]:
        current = self.get_patient(id_paciente)
        if current is None:
            raise ValueError("Paciente no encontrado.")
        data = _validate_patient_payload({**current, **payload})
        with self._connect() as conn:
            conn.execute(
                """
                UPDATE pacientes
                SET documento = ?, nombre = ?, apellido = ?, edad = ?, sexo = ?, fecha_nacimiento = ?, telefono = ?
                WHERE id = ?
                """,
                (
                    data["documento"],
                    data["nombre"],
                    data["apellido"],
                    data["edad"],
                    data["sexo"],
                    data["fecha_nacimiento"],
                    data["telefono"],
                    id_paciente,
                ),
            )
        patient = self.get_patient(id_paciente)
        if patient is None:
            raise RuntimeError("No se pudo recuperar el paciente actualizado.")
        return patient

    def delete_patient(self, id_paciente: int) -> None:
        with self._connect() as conn:
            conn.execute("UPDATE pacientes SET activo = 0 WHERE id = ?", (id_paciente,))

    def search_pacientes(self, query: str) -> List[Dict[str, Any]]:
        term = f"%{query.strip()}%"
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT * FROM pacientes
                WHERE activo = 1
                  AND (documento LIKE ? OR nombre LIKE ? OR apellido LIKE ?)
                ORDER BY id DESC
                LIMIT 25
                """,
                (term, term, term),
            ).fetchall()
        return [dict(row) for row in rows]

    def list_trabajadores(self) -> List[Dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute("SELECT * FROM trabajadores WHERE activo = 1 ORDER BY id DESC").fetchall()
        return [dict(row) for row in rows]

    def get_worker(self, worker_id: int) -> Optional[Dict[str, Any]]:
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM trabajadores WHERE id = ?", (worker_id,)).fetchone()
        return dict(row) if row else None

    def create_worker(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        data = _validate_worker_payload(payload)
        with self._connect() as conn:
            cursor = conn.execute(
                """
                INSERT INTO trabajadores (
                    documento, nombre, apellido, rol, specialty, edad, sexo, fecha_nacimiento, telefono, activo, fecha_creacion
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?)
                """,
                (
                    data["documento"],
                    data["nombre"],
                    data["apellido"],
                    data["rol"],
                    data["specialty"],
                    data["edad"],
                    data["sexo"],
                    data["fecha_nacimiento"],
                    data["telefono"],
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
                UPDATE trabajadores
                SET documento = ?, nombre = ?, apellido = ?, rol = ?, specialty = ?,
                    edad = ?, sexo = ?, fecha_nacimiento = ?, telefono = ?
                WHERE id = ?
                """,
                (
                    data["documento"],
                    data["nombre"],
                    data["apellido"],
                    data["rol"],
                    data["specialty"],
                    data["edad"],
                    data["sexo"],
                    data["fecha_nacimiento"],
                    data["telefono"],
                    worker_id,
                ),
            )
        worker = self.get_worker(worker_id)
        if worker is None:
            raise RuntimeError("No se pudo recuperar el trabajador actualizado.")
        return worker

    def delete_worker(self, worker_id: int) -> None:
        with self._connect() as conn:
            conn.execute("UPDATE trabajadores SET activo = 0 WHERE id = ?", (worker_id,))

    def list_consultorios(self) -> List[Dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute("SELECT * FROM consultorios WHERE activo = 1 ORDER BY nombre").fetchall()
        return [dict(row) for row in rows]

    def get_consultorio(self, consultorio_id: int) -> Optional[Dict[str, Any]]:
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM consultorios WHERE id = ?", (consultorio_id,)).fetchone()
        return dict(row) if row else None

    def create_consultorio(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        nombre = _required_text(payload.get("nombre"), "Nombre")
        floor = _required_text(payload.get("floor"), "Piso")
        equipment = _required_text(payload.get("equipment"), "Equipamiento")
        with self._connect() as conn:
            cursor = conn.execute(
                """
                INSERT INTO consultorios (nombre, floor, equipment, activo, fecha_creacion)
                VALUES (?, ?, ?, 1, ?)
                """,
                (
                    nombre,
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
        nombre = _required_text(data.get("nombre"), "Nombre")
        floor = _required_text(data.get("floor"), "Piso")
        equipment = _required_text(data.get("equipment"), "Equipamiento")
        with self._connect() as conn:
            conn.execute(
                """
                UPDATE consultorios
                SET nombre = ?, floor = ?, equipment = ?
                WHERE id = ?
                """,
                (
                    nombre,
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
            conn.execute("UPDATE consultorios SET activo = 0 WHERE id = ?", (consultorio_id,))

    def list_medicamentos(self) -> List[Dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute("SELECT * FROM medicamentos WHERE activo = 1 ORDER BY nombre").fetchall()
        return [dict(row) for row in rows]

    def get_medication(self, medication_id: int) -> Optional[Dict[str, Any]]:
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM medicamentos WHERE id = ?", (medication_id,)).fetchone()
        return dict(row) if row else None

    def create_medication(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        nombre = _required_text(payload.get("nombre"), "Nombre")
        description = _required_text(payload.get("description"), "Descripcion")
        precio = float(payload.get("precio") or 0)
        stock = int(payload.get("stock") or 0)
        if precio < 0:
            raise ValueError("Precio no puede ser negativo.")
        if stock < 0:
            raise ValueError("Stock no puede ser negativo.")
        with self._connect() as conn:
            cursor = conn.execute(
                """
                INSERT INTO medicamentos (nombre, description, precio, stock, activo, fecha_creacion)
                VALUES (?, ?, ?, ?, 1, ?)
                """,
                (
                    nombre,
                    description,
                    precio,
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
        nombre = _required_text(data.get("nombre"), "Nombre")
        description = _required_text(data.get("description"), "Descripcion")
        precio = float(data.get("precio") or 0)
        stock = int(data.get("stock") or 0)
        if precio < 0:
            raise ValueError("Precio no puede ser negativo.")
        if stock < 0:
            raise ValueError("Stock no puede ser negativo.")
        with self._connect() as conn:
            conn.execute(
                """
                UPDATE medicamentos
                SET nombre = ?, description = ?, precio = ?, stock = ?
                WHERE id = ?
                """,
                (
                    nombre,
                    description,
                    precio,
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
            conn.execute("UPDATE medicamentos SET activo = 0 WHERE id = ?", (medication_id,))

    # Aliases for compatibility
    def list_patients(self):
        return self.list_pacientes()

    def search_patients(self, query: str):
        return self.search_pacientes(query)

    def list_specialties(self):
        return self.list_especialidades()

    def list_appointments(self):
        return self.list_citas()

    def get_patient(self, id_paciente):
        rows = self.list_pacientes()
        for row in rows:
            if row['id'] == id_paciente:
                return row
        return None

    def get_appointment(self, id_cita):
        rows = self.list_citas()
        for row in rows:
            if row['id'] == id_cita:
                return row
        return None

    def set_active_triage(self, id_cita):
        return self.set_activo_triedad(id_cita)

    def capture_triage(self, id_cita, vitals, analysis, source):
        return self.capture_triedad(id_cita, vitals, analysis, source)

    def list_workers(self):
        return self.list_trabajadores()

    def list_medications(self):
        return self.list_medicamentos()

    def list_transactions(self):
        return self.list_transacciones()

    def create_transaction(
        self,
        modulo: str,
        tipo_referencia: str,
        id_referencia: int,
        documento_paciente: str,
        nombre_paciente: str,
        concepto: str,
        monto: float,
        metodo_pago: str = "Efectivo",
        creado_por: Optional[str] = None,
    ) -> Dict[str, Any]:
        with self._connect() as conn:
            return self._record_transaction(
                conn,
                modulo,
                tipo_referencia,
                id_referencia,
                documento_paciente,
                nombre_paciente,
                concepto,
                monto,
                metodo_pago,
                creado_por,
            )

    def update_user(self, user_id, payload):
        return None

    def create_user(self, payload):
        return None
    
    @staticmethod
    def _next_ticket(conn: sqlite3.Connection) -> str:
        count = conn.execute("SELECT COUNT(*) FROM citas").fetchone()[0] + 1
        return f"A{count:04d}"

    @staticmethod
    def _next_codigo_transaccion(conn: sqlite3.Connection, modulo: str) -> str:
        prefix = {"cashier": "CJ", "pharmacy": "FA"}.get(modulo, "TX")
        count = conn.execute(
            "SELECT COUNT(*) FROM transacciones WHERE modulo = ?", (modulo,)
        ).fetchone()[0] + 1
        return f"{prefix}-{datetime.now().strftime('%Y%m%d%H%M%S')}-{count:04d}"

    def _record_transaction(
        self,
        conn: sqlite3.Connection,
        modulo: str,
        tipo_referencia: str,
        id_referencia: int,
        documento_paciente: str,
        nombre_paciente: str,
        concepto: str,
        monto: float,
        metodo_pago: str = "Efectivo",
        creado_por: Optional[str] = None,
    ) -> Dict[str, Any]:
        # For pharmacy module, always create new transactions (no duplicate check)
        # This ensures each "Entregar" action creates a new transaction record
        if modulo != "pharmacy":
            existing = conn.execute(
                """
                SELECT *
                FROM transacciones
                WHERE modulo = ? AND tipo_referencia = ? AND id_referencia = ? AND estado = 'paid'
                LIMIT 1
                """,
                (modulo, tipo_referencia, id_referencia),
            ).fetchone()
            if existing:
                return dict(existing)

        conn.execute(
            """
            INSERT INTO transacciones (
                codigo_transaccion, modulo, tipo_referencia, id_referencia, documento_paciente,
                nombre_paciente, concepto, monto, metodo_pago, estado, creado_por, fecha_creacion
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'paid', ?, ?)
            """,
            (
                self._next_codigo_transaccion(conn, modulo),
                modulo,
                tipo_referencia,
                id_referencia,
                documento_paciente,
                nombre_paciente,
                concepto,
                max(0.0, float(monto or 0)),
                _required_text(metodo_pago or "Efectivo", "Metodo de pago"),
                creado_por or "",
                utc_now(),
            ),
        )
        row = conn.execute(
            "SELECT * FROM transacciones WHERE id = last_insert_rowid()"
        ).fetchone()
        return dict(row) if row else {}

    @staticmethod
    def _audit(
        conn: sqlite3.Connection,
        tipo_evento: str,
        entidad: str,
        id_entidad: Optional[int],
        mensaje: str,
    ) -> None:
        conn.execute(
            """
            INSERT INTO eventos_auditoria (tipo_evento, entidad, id_entidad, mensaje, fecha_creacion)
            VALUES (?, ?, ?, ?, ?)
            """,
            (tipo_evento, entidad, id_entidad, mensaje, utc_now()),
        )

    @staticmethod
    def _appointment_dict(
        row: sqlite3.Row,
        triedad: Optional[Dict[str, Any]],
        consultation: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        return {
            "id": row["id"],
            "ticket": row["ticket"],
            "estado": row["estado"],
            "estado_pago": row["estado_pago"],
            "estado_triaje": row["estado_triaje"],
            "estado_consulta": row["estado_consulta"],
            "estado_farmacia": row["estado_farmacia"],
            "consultorio": row["consultorio"],
            "room": row["consultorio"] or row["especialidad_nombre"] or "Sin consultorio",
            "fecha_programada": row["fecha_programada"],
            "codigo_recibo": row["codigo_recibo"],
            "fecha_creacion": row["fecha_creacion"],
            "fecha_pago": row["fecha_pago"],
            "patient": {
                "id": row["id_paciente"],
                "documento": row["documento_paciente"],
                "nombre": row["patient_nombre"],
                "apellido": row["patient_apellido"],
                "edad": row["patient_edad"],
                "sexo": row["patient_sexo"],
                "fecha_nacimiento": row["patient_fecha_nacimiento"],
                "telefono": row["patient_telefono"],
                "nombre_completo": f"{row['patient_nombre']} {row['patient_apellido']}",
            },
            "specialty": {
                "id": row["id_especialidad"],
                "nombre": row["especialidad_nombre"],
                "precio": row["specialty_precio"],
                "duracion_minutos": row["specialty_duracion_min"],
                "nombre_medico": row["especialidad_nombre_medico"],
            },
            "triedad": triedad,
            "consultation": consultation,
        }

    @staticmethod
    def _triedad_dict(row: sqlite3.Row) -> Dict[str, Any]:
        data = dict(row)
        data["analysis"] = json.loads(data.get("analisis_json") or "{}")
        # Aliases para compatibilidad con frontend
        data["predicted_systolic"] = data.get("sistolica_predicha")
        data["estimated_attention_minutes"] = data.get("minutos_estimados")
        data["risk_score"] = data.get("puntuacion_riesgo")
        data["risk_label"] = data.get("etiqueta_riesgo")
        data["decision_summary"] = data.get("resumen_decision")
        return data


class SupabaseRepository(BaseRepository):
    """REST adapter for Supabase. It expects supabase_schema.sql to be applied."""

    def __init__(self, url: str, clave: str) -> None:
        self.url = url.rstrip("/")
        self.clave = clave

    def setup(self) -> None:
        if not self.list_especialidades():
            for specialty in DEFAULT_SPECIALTIES:
                self._insert("especialidades", specialty)

    def snapshot(self) -> Dict[str, Any]:
        citas = self.list_citas()
        recetas = self.list_recetas()
        return {
            "especialidades": self.list_especialidades(),
            "citas": citas,
            "recetas": recetas,
            "stats": self._stats(citas, recetas),
            "activo_triedad_id_cita": self.get_setting("activo_triedad_id_cita"),
        }

    def list_especialidades(self) -> List[Dict[str, Any]]:
        return self._select("especialidades", {"select": "*", "order": "id.asc"})

    def get_appointment(self, id_cita: int) -> Optional[Dict[str, Any]]:
        return next(
            (item for item in self.list_citas() if int(item["id"]) == int(id_cita)),
            None,
        )

    def list_citas(self) -> List[Dict[str, Any]]:
        citas = self._select("citas", {"select": "*", "order": "id.desc"})
        pacientes = {item["id"]: item for item in self._select("pacientes", {"select": "*"})}
        especialidades = {item["id"]: item for item in self.list_especialidades()}
        triedad = {
            item["id_cita"]: self._triedad_dict(item)
            for item in self._select("expedientes", {"select": "*"})
        }
        consultas = {
            item["id_cita"]: item for item in self._select("consultas", {"select": "*"})
        }
        results = []
        for row in citas:
            patient = pacientes.get(row["id_paciente"], {})
            specialty = especialidades.get(row["id_especialidad"], {})
            results.append(
                {
                    **row,
                    "patient": {
                        **patient,
                        "nombre_completo": f"{patient.get('nombre', '')} {patient.get('apellido', '')}".strip(),
                    },
                    "specialty": specialty,
                    "room": row.get("consultorio") or specialty.get("nombre") or "Sin consultorio",
                    "triedad": triedad.get(row["id"]),
                    "consultation": consultas.get(row["id"]),
                }
            )
        return results

    def create_patient_and_appointment(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        documento = _validate_documento(payload.get("documento"))
        nombre = _required_text(payload.get("nombre"), "Nombres")
        apellido = _required_text(payload.get("apellido"), "Apellidos")
        edad = _validate_edad(payload.get("edad"))
        sexo = _required_text(payload.get("sexo") or "No especificado", "Sexo")
        telefono = _validate_telefono(payload.get("telefono"))
        id_especialidad = int(payload.get("id_especialidad") or 0)
        if id_especialidad <= 0:
            raise ValueError("Faltan datos obligatorios del paciente o especialidad.")

        existing = self._select(
            "pacientes", {"select": "*", "documento": f"eq.{documento}", "limit": "1"}
        )
        patient_payload = {
            "documento": documento,
            "nombre": nombre,
            "apellido": apellido,
            "edad": edad,
            "sexo": sexo,
            "telefono": telefono,
        }
        if existing:
            patient = self._patch("pacientes", {"id": f"eq.{existing[0]['id']}"}, patient_payload)[0]
        else:
            patient = self._insert("pacientes", {**patient_payload, "fecha_creacion": utc_now()})[0]

        ticket = self._next_ticket()
        appointment = self._insert(
            "citas",
            {
                "ticket": ticket,
                "id_paciente": patient["id"],
                "id_especialidad": id_especialidad,
                "estado": "registered",
                "estado_pago": "pending",
                "estado_triaje": "not_started",
                "estado_consulta": "not_started",
                "estado_farmacia": "none",
                "fecha_creacion": utc_now(),
            },
        )[0]
        self._audit("appointment_created", "citas", appointment["id"], f"Cita {ticket} registrada")
        result = self.get_appointment(int(appointment["id"]))
        if result is None:
            raise RuntimeError("No se pudo recuperar la cita creada.")
        return result

    def mark_paid(self, id_cita: int) -> Dict[str, Any]:
        appointment = self.get_appointment(id_cita)
        if not appointment:
            raise ValueError("Cita no encontrada.")
        if appointment["estado_pago"] == "paid":
            return appointment

        specialty = appointment["specialty"]
        paid_count = len(
            [
                item
                for item in self.list_citas()
                if item["id_especialidad"] == appointment["id_especialidad"]
                and item["estado_pago"] == "paid"
            ]
        )
        fecha_programada = local_now() + timedelta(minutes=(paid_count + 1) * int(specialty["duracion_minutos"]))
        codigo_recibo = f"B{datetime.now().strftime('%Y%m%d%H%M')}-{id_cita:04d}"
        self._patch(
            "citas",
            {"id": f"eq.{id_cita}"},
            {
                "estado": "paid",
                "estado_pago": "paid",
                "estado_triaje": "waiting",
                "estado_consulta": "not_started",
                "estado_farmacia": "none",
                "consultorio": specialty["consultorio"],
                "fecha_programada": fecha_programada.isoformat(timespec="minutes"),
                "codigo_recibo": codigo_recibo,
                "fecha_pago": utc_now(),
            },
        )
        self._audit("payment_registered", "citas", id_cita, f"Pago {codigo_recibo} confirmado")
        return self.get_appointment(id_cita) or appointment

    def set_activo_triedad(self, id_cita: int) -> Dict[str, Any]:
        appointment = self.get_appointment(id_cita)
        if not appointment:
            raise ValueError("Cita no encontrada.")
        if appointment.get("estado_pago") not in ("paid", "pagado"):
            raise ValueError("La cita debe estar pagada antes de triaje.")
        if appointment.get("estado_triaje") in ("done", "finalizado"):
            raise ValueError("El triaje ya fue registrado.")
        self._patch(
            "citas",
            {"id": f"eq.{id_cita}"},
            {"estado": "in_triedad", "estado_triaje": "in_progress"},
        )
        self.set_setting("activo_triedad_id_cita", str(id_cita))
        self._audit("triedad_started", "citas", id_cita, "Paciente activado para captura IoT")
        return self.get_appointment(id_cita) or appointment

    def capture_triedad(
        self,
        id_cita: int,
        vitals: Dict[str, Any],
        analysis: Dict[str, Any],
        fuente: str,
    ) -> Dict[str, Any]:
        existing = self._select(
            "expedientes",
            {"select": "*", "id_cita": f"eq.{id_cita}", "limit": "1"},
        )
        payload = {
            "id_cita": id_cita,
            "temperatura": float(vitals["temperatura"]),
            "ritmo_cardiaco": int(vitals["ritmo_cardiaco"]),
            "spo2": int(vitals["spO2"]),
            "sistolica": int(vitals["blood_pressure_sistolica"]),
            "diastolica": int(vitals["blood_pressure_diastolica"]),
            "peso": float(vitals["peso"]),
            "altura": float(vitals["altura"]),
            "imc": float(analysis["imc"]),
            "prioridad": analysis["prioridad"],
            "puntuacion_riesgo": float(analysis["risk_probability"]),
            "etiqueta_riesgo": analysis["etiqueta_riesgo"],
            "sistolica_predicha": float(analysis["sistolica_predicha"]),
            "minutos_estimados": float(analysis["minutos_estimados"]),
            "resumen_decision": analysis["resumen_decision"],
            "analisis_json": json.dumps(analysis),
            "fuente": fuente,
            "fecha_captura": utc_now(),
        }
        if existing:
            self._patch("expedientes", {"id": f"eq.{existing[0]['id']}"}, payload)
        else:
            self._insert("expedientes", payload)
        self._patch(
            "citas",
            {"id": f"eq.{id_cita}"},
            {"estado": "triedadd", "estado_triaje": "done", "estado_consulta": "waiting"},
        )
        if self.get_setting("activo_triedad_id_cita") == str(id_cita):
            self.set_setting("activo_triedad_id_cita", None)
        self._audit("triedad_captured", "expedientes", id_cita, f"Triaje {analysis['prioridad']} registrado")
        return self.get_appointment(id_cita) or {}

    def create_consultation(self, id_cita: int, payload: Dict[str, Any]) -> Dict[str, Any]:
        appointment = self.get_appointment(id_cita)
        if not appointment:
            raise ValueError("Cita no encontrada.")
        diagnostico = str(payload.get("diagnostico") or "").strip()
        if not diagnostico:
            raise ValueError("El diagnostico es obligatorio.")

        consultation_payload = {
            "id_cita": id_cita,
            "nombre_medico": str(payload.get("nombre_medico") or appointment["specialty"].get("nombre_medico") or ""),
            "sintomas": str(payload.get("sintomas") or ""),
            "diagnostico": diagnostico,
            "tratamiento_notas": str(payload.get("tratamiento_notas") or ""),
            "notas": str(payload.get("notas") or ""),
        }
        existing = self._select(
            "consultas",
            {"select": "*", "id_cita": f"eq.{id_cita}", "limit": "1"},
        )
        if existing:
            consultation = self._patch(
                "consultas", {"id": f"eq.{existing[0]['id']}"}, consultation_payload
            )[0]
        else:
            consultation = self._insert(
                "consultas", {**consultation_payload, "fecha_creacion": utc_now()}
            )[0]

        old_pending = self._select(
            "recetas",
            {
                "select": "*",
                "id_cita": f"eq.{id_cita}",
                "estado": "neq.dispensed",
            },
        )
        for item in old_pending:
            self._delete("recetas", {"id": f"eq.{item['id']}"})

        receta_items = [
            item for item in payload.get("receta_items") or [] if item.get("medicamento")
        ]
        id_receta = None
        if receta_items:
            total = sum(
                max(1, int(item.get("cantidad") or 1)) * max(0.0, float(item.get("unit_precio") or 0))
                for item in receta_items
            )
            prescription = self._insert(
                "recetas",
                {
                    "id_cita": id_cita,
                    "id_consulta": consultation["id"],
                    "estado": "pending",
                    "total": total,
                    "fecha_creacion": utc_now(),
                },
            )[0]
            id_receta = prescription["id"]
            for item in receta_items:
                self._insert(
                    "receta_items",
                    {
                        "id_receta": id_receta,
                        "medicamento": str(item.get("medicamento") or ""),
                        "dosis": str(item.get("dosis") or ""),
                        "frecuencia": str(item.get("frecuencia") or ""),
                        "dias": max(1, int(item.get("dias") or 1)),
                        "cantidad": max(1, int(item.get("cantidad") or 1)),
                        "unit_precio": max(0.0, float(item.get("unit_precio") or 0)),
                    },
                )

        self._patch(
            "citas",
            {"id": f"eq.{id_cita}"},
            {
                "estado": "prescription_pending" if id_receta else "completed",
                "estado_consulta": "done",
                "estado_farmacia": "pending" if id_receta else "none",
            },
        )
        self._audit("consultation_saved", "consultas", consultation["id"], "Consulta medica registrada")
        return self.get_appointment(id_cita) or appointment

    def dispense_prescription(
        self,
        id_receta: int,
        metodo_pago: str = "Efectivo",
        creado_por: Optional[str] = None,
    ) -> Dict[str, Any]:
        prescription = self._select(
            "recetas", {"select": "*", "id": f"eq.{id_receta}", "limit": "1"}
        )
        if not prescription:
            raise ValueError("Receta no encontrada.")
        row = prescription[0]
        self._patch(
            "recetas",
            {"id": f"eq.{id_receta}"},
            {"estado": "dispensed", "fecha_dispensacion": utc_now()},
        )
        self._patch(
            "citas",
            {"id": f"eq.{row['id_cita']}"},
            {"estado": "completed", "estado_farmacia": "dispensed"},
        )
        self._audit("prescription_dispensed", "recetas", id_receta, "Medicamentos entregados")
        # Return the prescription with basic info
        return {
            "id": id_receta,
            "id_cita": row.get("id_cita"),
            "estado": "dispensed",
            "total": row.get("total"),
            "id_consulta": row.get("id_consulta"),
        }

    def list_recetas(self) -> List[Dict[str, Any]]:
        recetas = self._select("recetas", {"select": "*", "order": "id.desc"})
        items = self._select("receta_items", {"select": "*", "order": "id.asc"})
        citas = {item["id"]: item for item in self.list_citas()}
        by_prescription: Dict[int, List[Dict[str, Any]]] = {}
        for item in items:
            by_prescription.setdefault(int(item["id_receta"]), []).append(item)
        results = []
        for prescription in recetas:
            appointment = citas.get(prescription["id_cita"], {})
            patient = appointment.get("patient", {})
            specialty = appointment.get("specialty", {})
            row = {
                **prescription,
                "ticket": appointment.get("ticket"),
                "nombre_paciente": patient.get("nombre_completo"),
                "documento_paciente": patient.get("documento"),
                "especialidad_nombre": specialty.get("nombre"),
                "consultorio": appointment.get("consultorio"),
                "diagnostico": (appointment.get("consultation") or {}).get("diagnostico"),
                "items": by_prescription.get(int(prescription["id"]), []),
            }
            # Map estado -> status para frontend
            raw = prescription.get("estado", "")
            if raw == "pendiente" or raw == "pending":
                row["status"] = "pending"
            elif raw == "dispensado" or raw == "dispensed":
                row["status"] = "dispensed"
            else:
                row["status"] = raw or ""
            results.append(row)
        return results

    def get_setting(self, clave: str) -> Optional[str]:
        rows = self._select("configuracion", {"select": "*", "clave": f"eq.{clave}", "limit": "1"})
        return rows[0]["valor"] if rows else None

    def set_setting(self, clave: str, valor: Optional[str]) -> None:
        if valor is None:
            self._delete("configuracion", {"clave": f"eq.{clave}"})
        elif self.get_setting(clave) is None:
            self._insert("configuracion", {"clave": clave, "valor": valor})
        else:
            self._patch("configuracion", {"clave": f"eq.{clave}"}, {"valor": valor})

    def _request(
        self,
        method: str,
        table: str,
        params: Optional[Dict[str, str]] = None,
        payload: Optional[Any] = None,
        prefer: Optional[str] = None,
    ) -> Any:
        headers = {
            "apiclave": self.clave,
            "Authorization": f"Bearer {self.clave}",
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
        if response.estado_code >= 400:
            raise RuntimeError(f"Supabase {table}: {response.estado_code} {response.text}")
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
        rows = self._select("citas", {"select": "id", "order": "id.desc", "limit": "1"})
        next_id = int(rows[0]["id"]) + 1 if rows else 1
        return f"A{next_id:04d}"

    def _audit(self, tipo_evento: str, entidad: str, entidad_id: Optional[int], mensaje: str) -> None:
        self._insert(
            "eventos_auditoria",
            {
                "tipo_evento": tipo_evento,
                "entidad": entidad,
                "entidad_id": entidad_id,
                "mensaje": mensaje,
                "fecha_creacion": utc_now(),
            },
        )
    
        # ============== CRUD for Workers ==============
    def list_trabajadores(self):
        conn = self._connect()
        rows = conn.execute('SELECT * FROM trabajadores WHERE activo = 1 ORDER BY id').fetchall()
        return [dict(row) for row in rows]

    def create_worker(self, payload):
        conn = self._connect()
        data = {
            'documento': payload.get('documento'),
            'nombre': payload.get('nombre'),
            'apellido': payload.get('apellido'),
            'rol': payload.get('rol'),
            'specialty': payload.get('specialty'),
            'telefono': payload.get('telefono'),
            'activo': 1,
            'fecha_creacion': utc_now()
        }
        conn.execute('''INSERT INTO trabajadores (documento, nombre, apellido, rol, specialty, telefono, activo, fecha_creacion)
            VALUES (:documento, :nombre, :apellido, :rol, :specialty, :telefono, :activo, :fecha_creacion)''', data)
        conn.commit()
        return self.get_worker(conn.lastrowid)

    def get_worker(self, worker_id):
        conn = self._connect()
        row = conn.execute('SELECT * FROM trabajadores WHERE id = ?', (worker_id,)).fetchone()
        return dict(row) if row else None

    def update_worker(self, worker_id, payload):
        conn = self._connect()
        conn.execute('''UPDATE trabajadores SET documento=:documento, nombre=:nombre, apellido=:apellido, 
            rol=:rol, specialty=:specialty, telefono=:telefono WHERE id=:id''', {**payload, 'id': worker_id})
        conn.commit()
        return self.get_worker(worker_id)

    def delete_worker(self, worker_id):
        conn = self._connect()
        conn.execute('UPDATE trabajadores SET activo = 0 WHERE id = ?', (worker_id,))
        conn.commit()

    # ============== CRUD for Consultorios ==============
    def list_consultorios(self):
        conn = self._connect()
        rows = conn.execute('SELECT * FROM consultorios WHERE activo = 1 ORDER BY id').fetchall()
        return [dict(row) for row in rows]

    def create_consultorio(self, payload):
        conn = self._connect()
        data = {'nombre': payload.get('nombre'), 'floor': payload.get('floor'), 'equipment': payload.get('equipment'), 
               'activo': 1, 'fecha_creacion': utc_now()}
        conn.execute('INSERT INTO consultorios (nombre, floor, equipment, activo, fecha_creacion) VALUES (:nombre, :floor, :equipment, :activo, :fecha_creacion)', data)
        conn.commit()
        return dict(conn.execute('SELECT * FROM consultorios WHERE id = ?', (conn.lastrowid,)).fetchone())

    def delete_consultorio(self, consultorio_id):
        conn = self._connect()
        conn.execute('UPDATE consultorios SET activo = 0 WHERE id = ?', (consultorio_id,))
        conn.commit()

    # ============== CRUD for Medications ==============
    def list_medicamentos(self):
        conn = self._connect()
        rows = conn.execute('SELECT * FROM medicamentos WHERE activo = 1 ORDER BY nombre').fetchall()
        return [dict(row) for row in rows]

    def create_medication(self, payload):
        conn = self._connect()
        data = {'nombre': payload.get('nombre'), 'description': payload.get('description'), 
               'precio': payload.get('precio', 0), 'stock': payload.get('stock', 0), 
               'activo': 1, 'fecha_creacion': utc_now()}
        conn.execute('INSERT INTO medicamentos (nombre, description, precio, stock, activo, fecha_creacion) VALUES (:nombre, :description, :precio, :stock, :activo, :fecha_creacion)', data)
        conn.commit()
        return dict(conn.execute('SELECT * FROM medicamentos WHERE id = ?', (conn.lastrowid,)).fetchone())

    def update_medication(self, medication_id, payload):
        conn = self._connect()
        conn.execute('''UPDATE medicamentos SET nombre=:nombre, description=:description, precio=:precio, stock=:stock WHERE id=:id''', 
            {**payload, 'id': medication_id})
        conn.commit()
        return dict(conn.execute('SELECT * FROM medicamentos WHERE id = ?', (medication_id,)).fetchone())

    def delete_medication(self, medication_id):
        conn = self._connect()
        conn.execute('UPDATE medicamentos SET activo = 0 WHERE id = ?', (medication_id,))
        conn.commit()

    # ============== Search Patients ==============
    def search_pacientes(self, query):
        conn = self._connect()
        rows = conn.execute('''SELECT * FROM pacientes WHERE documento LIKE ? OR nombre LIKE ? OR apellido LIKE ? LIMIT 20''',
            (f'%{query}%', f'%{query}%', f'%{query}%')).fetchall()
        return [dict(row) for row in rows]
    
    def get_patient(self, id_paciente):
        conn = self._connect()
        row = conn.execute('SELECT * FROM pacientes WHERE id = ?', (id_paciente,)).fetchone()
        return dict(row) if row else None

    def update_patient(self, id_paciente, payload):
        conn = self._connect()
        conn.execute("UPDATE pacientes SET documento=:documento, nombre=:nombre, apellido=:apellido, edad=:edad, sexo=:sexo, telefono=:telefono WHERE id=:id", 
            {**payload, 'id': id_paciente})
        conn.commit()
        return self.get_patient(id_paciente)

    def delete_patient(self, id_paciente):
        conn = self._connect()
        conn.execute('DELETE FROM pacientes WHERE id = ?', (id_paciente,))
        conn.commit()



    @staticmethod
    def _stats(citas: Sequence[Dict[str, Any]], recetas: Sequence[Dict[str, Any]]) -> Dict[str, int]:
        return {
            "registered": len(citas),
            "pending_payment": len([item for item in citas if item["estado_pago"] == "pending"]),
            "waiting_triedad": len([item for item in citas if item["estado_triaje"] in {"waiting", "in_progress"}]),
            "waiting_consultation": len([item for item in citas if item["estado_consulta"] == "waiting"]),
            "pending_pharmacy": len([item for item in recetas if item["estado"] == "pending"]),
            "completed": len([item for item in citas if item["estado"] == "completed"]),
        }

    @staticmethod
    def _triedad_dict(row: Dict[str, Any]) -> Dict[str, Any]:
        data = {**row, "analysis": json.loads(row.get("analisis_json") or "{}")}
        # Aliases para compatibilidad con frontend
        data["predicted_systolic"] = data.get("sistolica_predicha")
        data["estimated_attention_minutes"] = data.get("minutos_estimados")
        data["risk_score"] = data.get("puntuacion_riesgo")
        data["risk_label"] = data.get("etiqueta_riesgo")
        data["decision_summary"] = data.get("resumen_decision")
        return data

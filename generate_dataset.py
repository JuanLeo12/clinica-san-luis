"""
Generador de dataset para algoritmos de Machine Learning de la clínica.
Dataset basado en datos clínicos del triage: temperatura, frecuencia cardíaca, SpO2,
presión arterial, peso, altura, edad -> priorización y minutos de atención.
"""

import csv
import random
from pathlib import Path

try:
    import openpyxl
    HAS_OPENPYXL = True
except ImportError:
    HAS_OPENPYXL = False

def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def _save_excel(path: Path, headers: list, rows: list) -> None:
    """Guarda el dataset en formato Excel (.xlsx)."""
    if not HAS_OPENPYXL:
        print("Advertencia: openpyxl no esta instalado. Guardando como CSV.")
        csv_path = path.with_suffix(".csv")
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(headers)
            writer.writerows(rows)
        print(f"  (guardado como CSV): {csv_path}")
        return

    from openpyxl import Workbook
    wb = Workbook()
    ws = wb.active
    ws.title = "Triage Dataset"
    ws.append(headers)
    for row in rows:
        ws.append(row)
    wb.save(path)
    print(f"  - Excel: {path}")


def generate_triage_dataset(num_samples: int = 500, output_file: str = "triage_dataset.csv"):
    """Genera un dataset de triage con datos clínicos realisticas para ML."""

    random.seed(42)
    data_rows = []
    headers = [
        "edad",                          # Edad del paciente (años)
        "temperatura",                   # Temperatura corporal (°C)
        "ritmo_cardiaco",                # Frecuencia cardíaca (lpm)
        "spo2",                         # Saturación de oxígeno (%)
        "presion_sistolica",             # Presión arterial sistólica (mmHg)
        "presion_diastolica",           # Presión arterial diastólica (mmHg)
        "peso",                        # Peso (kg)
        "altura",                      # Altura (cm)
        "imc",                        # Índice de masa corporal
        "riesgo_binario",              # 1=alto/moderado riesgo, 0=bajo riesgo
        "prioridad",                   # Emergencia, Urgente, Preferente, Rutina
        "minutos_estimados",           # Minutos estimados de atención
    ]
    data_rows.append(headers)

    for _ in range(num_samples):
        age = random.randint(6, 88)
        temperature = round(random.uniform(35.2, 39.8), 1)
        heart_rate = random.randint(48, 142)
        spo2 = random.randint(86, 100)
        systolic = int(96 + (heart_rate - 70) * 0.42 + age * 0.23 + random.gauss(0, 8))
        diastolic = int(62 + (heart_rate - 70) * 0.18 + age * 0.08 + random.gauss(0, 5))
        weight = round(random.uniform(18.0, 90.0), 1)
        height = random.randint(100, 195)
        bmi = weight / ((height / 100) ** 2)

        # Clasificar riesgo
        high_risk = (
            temperature >= 39.0
            or temperature <= 35.5
            or heart_rate >= 125
            or heart_rate <= 45
            or spo2 <= 91
            or systolic >= 155
            or diastolic >= 100
        )
        moderate_risk = (
            temperature >= 37.8
            or heart_rate >= 105
            or spo2 <= 94
            or systolic >= 140
            or diastolic >= 90
        )

        if high_risk:
            priority = "Emergencia"
            risk_binary = 1
        elif moderate_risk:
            priority = "Urgente"
            risk_binary = 1
        elif age >= 65 or bmi >= 32:
            priority = "Preferente"
            risk_binary = 0
        else:
            priority = "Rutina"
            risk_binary = 0

        # Estimar minutos de atención
        minutes = (
            14
            + (6 if priority == "Emergencia" else 0)
            + (4 if priority == "Urgente" else 0)
            + max(0, 96 - spo2) * 0.9
            + max(0, temperature - 37.5) * 2.2
            + max(0, heart_rate - 100) * 0.08
            + random.gauss(0, 1.6)
        )
        minutes = _clamp(minutes, 8, 45)

        row = [
            age,
            temperature,
            heart_rate,
            spo2,
            systolic,
            diastolic,
            weight,
            height,
            round(bmi, 2),
            risk_binary,
            priority,
            round(minutes, 1),
        ]
        data_rows.append(row)

    output_path = Path(__file__).parent / output_file

    # Detectar formato por extensión
    if output_path.suffix.lower() == ".xlsx":
        _save_excel(output_path, headers, data_rows)
        print(f"Dataset generado: {output_path}")
    else:
        # CSV por defecto
        with open(output_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerows(data_rows)
        print(f"Dataset generado: {output_path}")

    print(f"  - Muestras: {num_samples}")
    print(f"  - Características: {len(headers) - 3} (variables de entrada)")
    print(f"  - Variables objetivo: 3 (riesgo_binario, prioridad, minutos_estimados)")

    # También generar versión Excel si no existe
    excel_path = output_path.with_suffix(".xlsx")
    if output_path.suffix.lower() != ".xlsx" and not excel_path.exists():
        print("\nGenerando versión Excel...")
        _save_excel(excel_path, headers, data_rows[1:])

    return output_path


if __name__ == "__main__":
    import sys
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 500
    file = sys.argv[2] if len(sys.argv) > 2 else "triage_dataset.csv"
    generate_triage_dataset(n, file)
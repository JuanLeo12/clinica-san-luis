# Clínica San Luis - Sistema de Gestión

Sistema web para automatizar el flujo interno de una clínica médica.

## Funcionalidades

- **Recepción**: Registro de pacientes y selección de especialidad
- **Caja**: Pago de consulta, emisión de comprobante, asignacion de consultorio y horario
- **Triaje**: Captura de signos vitales (manual o desde IoT)
- **Consultorio Médico**: Revision de triaje, diagnostico y receta digital
- **Farmacia**: Cobro y entrega de medicamentos
- **Pantalla de Turnos**: Muestra pacientes llamados a triaje y consulta
- **Admin**: Panel de control con historial de pacientes

## Tecnologias

- **Backend**: Flask (Python)
- **Base de datos**: SQLite
- **Frontend**: Vanilla JavaScript

---

## Ejecución rapida

### 1. Clonar repositorio

```bash
git clone https://github.com/JuanLeo12/clinica-san-luis.git
cd clinica-san-luis
```

### 2. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 3. Ejecutar

```bash
python app.py
```

### 4. Acceder

Abrir en el navegador: `http://localhost:5000`

---

## Configuracion

El proyecto usa un archivo `.env` con configuracion por defecto.

### Variable

| Variable            | Descripcion                                                       |
| ------------------- | ----------------------------------------------------------------- |
| `CONSULTADNI_TOKEN` | Token de [consultadni.com](https://www.consultadni.com/dev/login) |

---

## Roles de usuario

| Modulo    | Descripcion                             |
| --------- | --------------------------------------- |
| Recepcion | Registrar paciente y cobrar consulta    |
| Caja      | Confirmar pago y asignar consultorio    |
| Triaje    | Capturar signos vitales                 |
| Medico    | Atender paciente, diagnosticar, recetar |
| Farmacia  | Entregar medicamentos                   |
| Display   | Pantalla de turnos                      |
| Admin     | Ver todos los pacientes                 |

---

## Simulación IoT (Wokwi)

Para probar el hardware sin necesidad fisica:

### Requisitos

- Extension **Wokwi Simulation** en VS Code

### Ejecución

1. Abrir el archivo `diagram.json` y presionar **Play** (inicia simulador)
2. Abrir otra terminal y ejecutar:

```bash
./subir_codigo.bat
```

3. El simulador enviara datos al sistema

---

## Tech Stack

- Python 3.10+
- Flask 3.x
- SQLite

## Licencia

MIT

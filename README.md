# Sistema web de clinica con triaje IoT

Aplicacion Flask para automatizar el flujo interno de una clinica:

- Recepcion: registro del paciente y especialidad.
- Caja: pago, comprobante, consultorio y horario.
- Triaje: captura IoT o manual de signos vitales.
- Consultorio: revision de triaje, diagnostico y receta digital.
- Farmacia: cobro y entrega de medicamentos.
- Pantalla: turnos actuales para triaje y consultorio.
- IA: modelos en Python para apoyar priorizacion.

## Algoritmos incluidos

El archivo `clinic_ai.py` implementa en Python, sin dependencias externas:

- Machine learning aplicado a signos vitales.
- Regresion lineal simple para estimar presion sistolica esperada.
- Regresion lineal multiple para estimar minutos de consulta.
- Regresion logistica para probabilidad de riesgo clinico.
- Arbol de decision para prioridad de atencion.

## Ejecutar localmente

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

Abrir `http://localhost:5000`.

Por defecto usa SQLite en `clinic_app.sqlite3`. Para apuntar a otro archivo:

```bash
set DATABASE_PATH=clinic_app.sqlite3
set CONSULTADNI_TOKEN=TU_TOKEN_DE_CONSULTADNI
python app.py
```

## Usar Supabase

1. Crear un proyecto en Supabase.
2. Ejecutar `supabase_schema.sql` en el SQL Editor.
3. Configurar variables de entorno:

```bash
set APP_STORAGE=supabase
set SUPABASE_URL=https://TU-PROYECTO.supabase.co
set SUPABASE_SERVICE_ROLE_KEY=TU_SERVICE_ROLE_KEY
python app.py
```

Usar la service role key solo en backend. No debe exponerse en JavaScript.

## Conectar Wokwi

En `main.py`, cambiar:

```python
SERVER_URL = "http://TU_HOST/api/data"
```

Para local normalmente se usa una URL publica temporal como ngrok o el dominio desplegado, porque Wokwi no siempre puede llegar a `localhost` de tu PC.

## Desplegar en Vercel

El proyecto incluye:

- `api/index.py` como entrada WSGI.
- `vercel.json` para reescribir rutas a Flask.
- `public/static` para los archivos CSS y JS.

En Vercel configurar estas variables:

```bash
APP_STORAGE=supabase
SUPABASE_URL=https://TU-PROYECTO.supabase.co
SUPABASE_SERVICE_ROLE_KEY=TU_SERVICE_ROLE_KEY
CONSULTADNI_TOKEN=TU_TOKEN_DE_CONSULTADNI
```

Luego desplegar conectando el repositorio o con:

```bash
vercel deploy
```

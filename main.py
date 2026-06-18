import network
import time
import urequests
import ujson
from machine import Pin, ADC, I2C

import dht
import ssd1306
from hx711 import HX711

print("=== Simulador IoT Clínico (Wokwi) - Telemetría Estable ===")

# --- CONFIGURACION DE SENSORES Y ACTUADORES ---
sensor_dht = dht.DHT22(Pin(13))

potenciometro_hr = ADC(Pin(34))
potenciometro_hr.atten(ADC.ATTN_11DB) 

led_alerta = Pin(2, Pin.OUT)
led_alerta.value(0) 

try:
    i2c = I2C(0, scl=Pin(22), sda=Pin(21))
    pantalla = ssd1306.SSD1306_I2C(128, 64, i2c)
    pantalla.fill(0)
    pantalla.text("Iniciando...", 0, 0)
    pantalla.show()
except Exception as e:
    print("Error iniciando OLED:", e)
    pantalla = None

sensor_peso = HX711(16, 17)

pin_trig = Pin(12, Pin.OUT)
pin_echo = Pin(14, Pin.IN)

print("Conectando a red Wokwi-GUEST...")
sta_if = network.WLAN(network.STA_IF)
sta_if.active(True)
sta_if.connect('Wokwi-GUEST', '')

while not sta_if.isconnected():
    print(".", end="")
    time.sleep(0.5)
print("\n¡WiFi Conectado!")

# IMPORTANTE: Cambia esta IP por la de tu computadora
SERVER_URL = "http://LAPTOP-JEQK5077:5000/api/data"

# --- VARIABLES GLOBALES PARA CONGELAR LOS DATOS (BANDA MUERTA) ---
ultimo_peso_fijo = 0.0
ultima_talla_fija = 0.0
ultimo_hr_fijo = 75
ultima_temp_fija = 0.0

def medir_talla_cruda():
    """Mide la distancia y retorna la talla ignorando los bloqueos por Wi-Fi"""
    try:
        pin_trig.off()
        time.sleep_us(2)
        pin_trig.on()
        time.sleep_us(10)
        pin_trig.off()
        
        timeout = 30000
        start = time.ticks_us()
        while pin_echo.value() == 0:
            if time.ticks_diff(time.ticks_us(), start) > timeout: return -1.0
                
        pulse_start = time.ticks_us()
        while pin_echo.value() == 1:
            if time.ticks_diff(time.ticks_us(), pulse_start) > timeout: return -1.0
        pulse_end = time.ticks_us()
        
        duracion = time.ticks_diff(pulse_end, pulse_start)
        distancia_cm = (duracion * 0.0343) / 2
        return 220.0 - distancia_cm 
    except Exception:
        return -1.0
    
def evaluar_estado_paciente(temperatura, ritmo_cardiaco):

    mensaje = "PACIENTE OK"
    critico = False

    # Condiciones críticas
    if temperatura > 39.0:
        mensaje = "FIEBRE ALTA"
        critico = True

    elif temperatura < 35.0:
        mensaje = "HIPOTERMIA"
        critico = True

    elif ritmo_cardiaco > 130:
        mensaje = "TAQUICARDIA"
        critico = True

    elif ritmo_cardiaco < 40:
        mensaje = "BRADICARDIA"
        critico = True

    # Alertas moderadas
    elif temperatura > 37.5:
        mensaje = "FIEBRE"

    elif temperatura < 35.5:
        mensaje = "TEMP BAJA"

    elif ritmo_cardiaco > 100:
        mensaje = "FC ALTA"

    elif ritmo_cardiaco < 50:
        mensaje = "FC BAJA"

    return mensaje, critico

def capturar_datos_sensores():
    global ultimo_peso_fijo
    global ultima_talla_fija
    global ultimo_hr_fijo
    global ultima_temp_fija

    # 1. Temperatura
    try:
        sensor_dht.measure()
        temp_ambiente = sensor_dht.temperature()

        # Simulación de temperatura corporal
        temp_cruda = round(36.5 + ((temp_ambiente - 24.0) * 0.4), 1)
        
        if ultima_temp_fija == 0.0:
            ultima_temp_fija = temp_cruda

        # Solo actualizar si el cambio es clínicamente relevante
        if abs(temp_cruda - ultima_temp_fija) >= 0.3:
            ultima_temp_fija = temp_cruda

        temperatura = ultima_temp_fija

    except Exception:
        temperatura = ultima_temp_fija
        
    # 2. Ritmo Cardíaco (Más estricto)
    valor_pot_hr = potenciometro_hr.read()
    hr_crudo = int(50 + (valor_pot_hr / 4095) * 110)
    # Filtro: Solo cambia si la perilla se movió significativamente
    if abs(hr_crudo - ultimo_hr_fijo) > 5: 
        ultimo_hr_fijo = hr_crudo
    ritmo_cardiaco = ultimo_hr_fijo

    # 3. SpO2 y Presión (Cálculos estáticos basados en el ritmo cardiaco fijo)
    # Ya no hay cambios a menos que el ritmo cardíaco cambie
    if ritmo_cardiaco < 90:
        spo2 = 98
    elif ritmo_cardiaco < 110:
        spo2 = 96
    else:
        spo2 = 94
    
    # Presión fija basada en el ritmo cardiaco "congelado"
    blood_pressure_systolic = 115 + int((ritmo_cardiaco - 75) * 0.5)
    blood_pressure_diastolic = 75 + int((ritmo_cardiaco - 75) * 0.2)

    # 4. Peso (Filtro clínico realista)

    lecturas_peso = []

    for _ in range(10):
        val = sensor_peso.read()
        if val != 0:
            lecturas_peso.append(val)

    if len(lecturas_peso) > 0:

        lecturas_peso.sort()

        peso_crudo = round(
            max(0.0, (lecturas_peso[len(lecturas_peso)//2] / 420.0) * 3),
            1
        )
        print("Peso crudo:", peso_crudo)
        print("Peso fijo :", ultimo_peso_fijo)

        # Rango válido para pacientes
        if 30.0 <= peso_crudo <= 250.0:

            # Primera lectura
            if ultimo_peso_fijo == 0.0:
                ultimo_peso_fijo = peso_crudo

            else:

                cambio = abs(peso_crudo - ultimo_peso_fijo)

                # Ignorar pequeñas variaciones del sensor
                if cambio >= 2.0:
                    ultimo_peso_fijo = peso_crudo

    # 5. Talla (Aumentamos tolerancia de cambio a 3cm)
    lecturas_talla = []
    for _ in range(5):
        val = medir_talla_cruda()
        if val != -1.0: lecturas_talla.append(val)
            
    if len(lecturas_talla) > 0:
        lecturas_talla.sort()
        talla_cruda = max(0.0, min(230.0, round(lecturas_talla[len(lecturas_talla)//2], 1)))
        if abs(talla_cruda - ultima_talla_fija) > 3.0:
            ultima_talla_fija = talla_cruda

    return {
        "temperature": temperatura,
        "heart_rate": ritmo_cardiaco,
        "spO2": spo2,
        "blood_pressure_systolic": blood_pressure_systolic,
        "blood_pressure_diastolic": blood_pressure_diastolic,
        "weight": ultimo_peso_fijo,
        "height": ultima_talla_fija
    }

ultimo_envio = time.time()

while True:
    data = capturar_datos_sensores()
    mensaje_alerta, estado_critico = evaluar_estado_paciente(
        data["temperature"],
        data["heart_rate"]
    )

    # Control del LED rojo
    if estado_critico:
        led_alerta.value(1)
    else:
        led_alerta.value(0)    
    print("---------------------------------")
    print("Enviando datos ESTABLES al dashboard:", data)

    # --- ENVIO AUTOMATICO CADA SEGUNDO ---
    if SERVER_URL != "http://TU_IP_LOCAL:5000/api/data":
        try:
            cabeceras = {"Content-Type": "application/json"}
            payload = ujson.dumps(data)
            
            try:
                response = urequests.post(SERVER_URL, json=data, headers=cabeceras, timeout=5)
            except Exception:
                response = urequests.post(SERVER_URL, data=payload, headers=cabeceras, timeout=5)

            if response.status_code >= 200 and response.status_code < 300:
                ultimo_envio = time.time()
            response.close()
        except Exception as e:
            print("Error HTTP/Red:", e)

    # --- ACTUALIZAR PANTALLA OLED ---
    if pantalla:
        if (time.time() - ultimo_envio) > 10:
            try: pantalla.poweroff()
            except Exception: pass
        else:
            try: pantalla.poweron()
            except Exception: pass

            pantalla.fill(0) 
            pantalla.text("MONITOR PACIENTE", 0, 0)
            pantalla.text("T:{:.1f}C HR:{}bpm".format(data["temperature"], data["heart_rate"]), 0, 12)
            pantalla.text("SpO2:{}% P:{}/{}".format(data["spO2"], data["blood_pressure_systolic"], data["blood_pressure_diastolic"]), 0, 24)
            pantalla.text("Peso: {} kg".format(data["weight"]), 0, 36)
            pantalla.text("Alt: {} cm".format(data["height"]), 0, 46)
            
            if estado_critico:
                pantalla.text("CRITICO", 0, 56)

            elif mensaje_alerta != "PACIENTE OK":
                pantalla.text(mensaje_alerta, 0, 56)

            else:
                pantalla.text("PACIENTE OK", 0, 56)
                
            pantalla.show()
        
    time.sleep(1)
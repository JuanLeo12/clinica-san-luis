import sqlite3
import random

conn = sqlite3.connect('clinic_app.sqlite3')
conn.row_factory = sqlite3.Row

# Diagnosticos y medicamentos por especialidad
data_by_specialty = {
    1: {  # Medicina General
        'sintomas': ['Fiebre y dolor de cabeza', 'Dolor muscular general', 'Resfriado con congestión', 'Dolor abdominal', 'Cansancio general'],
        'diagnosticos': ['Infección respiratoria viral', 'Gripe comunitaria', 'Gastritis aguda', 'Anemia leve', 'Estrés laboral'],
        'medicamentos': ['Paracetamol 500 mg', 'Ibuprofeno 400 mg', 'Amoxicilina 500 mg', 'Loratadina 10 mg', 'Omeprazol 20 mg'],
    },
    2: {  # Pediatría
        'sintomas': ['Fiebre en niño', 'Tos con flema', 'Dolor de garganta', 'Erupción cutánea', 'Vómito y diarrea'],
        'diagnosticos': ['Infección respiratoria aguda', 'Amigdalitis bacteriana', 'Gastroenteritis infantil', 'Alergia alimentaria', 'Varicela'],
        'medicamentos': ['Azitromicina 250 mg', 'Cetirizina 5 mg', 'Sulbutamol 2 mg', 'Nistatina suspensión', 'Sales rehidratación ORS'],
    },
    3: {  # Cardiología
        'sintomas': ['Dolor en el pecho', 'Palpitaciones', 'Falta de aire', 'Mareos', 'Hinchazón de piernas'],
        'diagnosticos': ['Hipertensión arterial', 'Insuficiencia cardíaca', 'Arritmia cardíaca', 'Cardiopatía isquémica', 'Angina de pecho'],
        'medicamentos': ['Atorvastatina 20 mg', 'Carvedilol 12.5 mg', 'Enalapril 10 mg', 'Amlodipino 5 mg', 'Aspirina 100 mg'],
    },
    4: {  # Dermatología
        'sintomas': ['Erupción en la piel', 'Picazón intensa', 'Manchas en la piel', 'Acné facial', 'Lesión en la uña'],
        'diagnosticos': ['Dermatitis atópica', 'Psoriasis', 'Acné vulgar', 'Onicomicosis', 'Tiña corporal'],
        'medicamentos': ['Clotrimazol crema 1%', 'Hidrocortisona 1%', 'Mometasona crema', 'Benzoyl peroxide 5%', 'Tretinoína 0.025%'],
    },
    5: {  # Ginecología
        'sintomas': ['Dolor menstrual', 'Sangrado irregular', 'Flujo vaginal', 'Dolores pélvicos', 'Náuseas matutinas'],
        'diagnosticos': ['Menorragia', 'Embarazo ectópico', 'Candidiasis vaginal', 'Endometriosis', 'Embarazo primer trimestre'],
        'medicamentos': ['Levonorgestrel 1.5 mg', 'Progesterona 200 mg', 'Ácido fólico 5 mg', 'Clotrimazol óvulos', 'Hierro sulfato 300 mg'],
    },
    6: {  # Traumatología
        'sintomas': ['Dolor en la rodilla', 'Dolor de espalda', 'Esguince de tobillo', 'Dolor articular', 'Fractura suspecta'],
        'diagnosticos': ['Esguince lumbar', 'Artrosis de rodilla', 'Lesión deportiva', 'Bursitis', 'Lumbalgia crónica'],
        'medicamentos': ['Diclofenaco gel', 'Ketorolaco 30 mg', 'Glucosamina sulfato', 'Calcium D3', 'Meloxicam 15 mg'],
    },
    7: {  # Oftalmología
        'sintomas': ['Ojo rojos', 'Visión borrosa', 'Ojo seco', 'Secreción ocular', 'Dolor ocular'],
        'diagnosticos': ['Conjuntivitis alérgica', 'Ojo seco crónico', 'Blefaritis', 'Úlcera corneal', 'Glaucoma sospecha'],
        'medicamentos': ['Timolol 0.5%', 'Lágrimas artificiales', 'Tobramdex gotas', 'Cromoglicato 2%', 'Moxifloxacino gotas'],
    },
    8: {  # Neurología
        'sintomas': ['Dolor de cabeza intenso', 'Mareos', 'Pérdida de equilibrio', 'Entumecimiento', 'Convulsiones'],
        'diagnosticos': ['Migraña con aura', 'Epilepsia', 'Vértigo periférico', 'Neuropatía periférica', 'Enfermedad de Parkinson'],
        'medicamentos': ['Rizatriptan 5 mg', 'Levetiracetam 500 mg', 'Valproato 500 mg', 'Pregabalina 75 mg', 'Topiramato 50 mg'],
    },
    9: {  # Psiquiatría
        'sintomas': ['Tristeza persistente', 'Ansiedad excesiva', 'Insomnio', 'Aislamiento', 'Alucinaciones'],
        'diagnosticos': ['Episodio depresivo mayor', 'Trastorno de ansiedad', 'Insomnio crónico', 'Esquizofrenia', 'Trastorno bipolar'],
        'medicamentos': ['Sertralina 50 mg', 'Fluoxetina 20 mg', 'Escitalopram 10 mg', 'Quetiapina 25 mg', 'Alprazolam 0.5 mg'],
    },
    10: {  # Otorrinolaringología
        'sintomas': ['Dolor de oído', 'Congestión nasal', 'Dolor de garganta', 'Sangrado nasal', 'Pérdida de audición'],
        'diagnosticos': ['Otitis media', 'Rinosinusitis', 'Amigdalitis', 'Epistaxis', 'Sordera conductiva'],
        'medicamentos': ['Pseudofedrina 30 mg', 'Xylometazolina gotas', 'Amoxicilina clavulanato', 'Triamcinolona nasal', 'Carbocisteína jarabe'],
    },
    11: {  # Urología
        'sintomas': ['Dolor al orinar', 'Sangre en orina', 'Urgencia urinaria', 'Dolor prostático', 'Incontinencia'],
        'diagnosticos': ['Infección urinaria', 'Cálculo renal', 'Hiperplasia prostática', 'Cistitis', 'Prostatitis'],
        'medicamentos': ['Tamsulosina 0.4 mg', 'Finasterida 5 mg', 'Oxibutinina 5 mg', 'Ciprofloxacino 500 mg', 'Nitrofurantoína 100 mg'],
    },
    12: {  # Endocrinología
        'sintomas': ['Sed excesiva', 'Pérdida de peso', 'Fatiga', 'Bocio', 'Intolerancia al frío'],
        'diagnosticos': ['Diabetes mellitus tipo 2', 'Hipotiroidismo', 'Hipertiroidismo', 'Obesidad grado I', 'Síndrome metabólico'],
        'medicamentos': ['Levotiroxina 100 mcg', 'Metformina 850 mg', 'Glimepirida 4 mg', 'Sitagliptina 100 mg', 'Empagliflozina 10 mg'],
    },
    13: {  # Neumología
        'sintomas': ['Tos persistente', 'Falta de aire', 'Sibilancias', 'Dolor torácico', 'Expulsión de sangre'],
        'diagnosticos': ['Asma bronquial', 'EPOC', 'Neumonía', 'Bronquiectasias', 'Tuberculosis'],
        'medicamentos': ['Fluticasona aerosol', 'Salbutamol inhaler', 'Budesonida nebulización', 'Montelukast 10 mg', 'Azitromicina 500 mg'],
    },
    14: {  # Gastroenterología
        'sintomas': ['Acidez', 'Dolor abdominal', 'Diarrea', 'Estreñimiento', 'Náuseas'],
        'diagnosticos': ['Enfermedad por reflujo', 'Úlcera péptica', 'SII tipo Estreñimiento', 'Gastritis crónica', 'Colitis ulcerosa'],
        'medicamentos': ['Pantoprazol 40 mg', 'Esomeprazol 20 mg', 'Domperidona 10 mg', 'Loperamida 2 mg', 'Lactulosa jarabe'],
    },
    15: {  # Reumatología
        'sintomas': ['Dolor articular', 'Rigidez matutina', 'Hinchazón articular', 'Deformidad articular', 'Fatiga muscular'],
        'diagnosticos': ['Artritis reumatoide', 'Osteoartritis', 'Lupus eritematoso', 'Gota úrica', 'Fibromialgia'],
        'medicamentos': ['Etanercept 50 mg', 'Metotrexate 15 mg', 'Sulfasalazina 500 mg', 'Hydroxychloroquine 200 mg', 'Allopurinol 300 mg'],
    },
    16: {  # Angiología
        'sintomas': ['Piernas hinchadas', 'Venas visibles', 'Dolor en piernas', 'Úlceras en pierna', 'Frialdad extremities'],
        'diagnosticos': ['Insuficiencia venosa', 'Varices', 'Trombosis venosa', 'Úlcera varicosa', 'Enfermedad arterial periférica'],
        'medicamentos': ['Pentoxifilina 400 mg', 'Cilostazol 100 mg', 'Diosmina 500 mg', 'Rivaroxaban 20 mg', 'Aspirina protect'],
    },
}

# Obtener citas existentes que no tienen consulta
citas = conn.execute('''
    SELECT c.id, c.id_especialidad, c.ticket, c.id_paciente,
           p.nombre as nombre_paciente, p.apellido as apellido_paciente
    FROM citas c
    JOIN pacientes p ON c.id_paciente = p.id
    WHERE c.id NOT IN (SELECT id_cita FROM consultas)
    ORDER BY c.id
    LIMIT 50
''').fetchall()

print(f'=== CREANDO CONSULTAS Y RECETAS PARA {len(citas)} CITAS ===')

for cita in citas:
    id_cita = cita['id']
    id_esp = cita['id_especialidad']
    ticket = cita['ticket']
    paciente = f"{cita['nombre_paciente']} {cita['apellido_paciente']}"

    esp_data = data_by_specialty.get(id_esp, data_by_specialty[1])

    sintomas = random.choice(esp_data['sintomas'])
    diagnostico = random.choice(esp_data['diagnosticos'])
    medicamentos = random.sample(esp_data['medicamentos'], k=random.randint(2, 4))
    tratamiento = f"Tratamiento: {', '.join(medicamentos[:2])}"

    # Crear consulta primero
    conn.execute('''
        INSERT INTO consultas (id_cita, sintomas, diagnostico, tratamiento, nombre_medico)
        VALUES (?, ?, ?, ?, ?)
    ''', (id_cita, sintomas, diagnostico, tratamiento, 'Sistema'))

    id_consulta = conn.lastrowid

    # Crear receta enlazada a la consulta
    total = random.uniform(15, 150)
    estado = 'dispensado'

    conn.execute('''
        INSERT INTO recetas (id_cita, id_consulta, estado, total, fecha_creacion)
        VALUES (?, ?, ?, ?, datetime('now'))
    ''', (id_cita, id_consulta, estado, total))

    id_receta = conn.lastrowid

    # Agregar Items a la receta
    for med in medicamentos:
        cantidad = random.randint(1, 3)
        precio_unit = random.uniform(0.5, 8.0)

        conn.execute('''
            INSERT INTO receta_items (id_receta, medicina, dosis, frecuencia, dias, cantidad, precio_unitario)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (id_receta, med, '1 comprimido', 'Cada 8 horas', random.randint(5, 15), cantidad, precio_unit))

    print(f'Cita {ticket}: {diagnostico[:30]} -> {len(medicamentos)} medicamentos')

conn.commit()
print(f'\nTOTAL CREADO: {len(citas)}')
conn.close()
print('Consultas y recetas creadas correctamente!')
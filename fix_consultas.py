import sqlite3
import random

conn = sqlite3.connect('clinic_app.sqlite3')

# Data específico POR ESPECIALIDAD
data = {
    1: {  # Medicina General
        'sintomas': [
            'Fiebre mayor a 38°C con escalofríos',
            'Dolor de cabeza tensional',
            ' Tos seca persistente por 3 días',
            'Dolor abdominal difuso',
            'Cansancio y debilidad general',
            'Dolor de garganta al tragar',
            'Congestión nasal y rinorrea',
            'Dolores musculares generalizados'
        ],
        'diagnosticos': [
            'Infección respiratoria aguda',
            'Gripe comunitaria',
            'Gastritis aguda',
            'Anemia por deficiencia de hierro',
            'Síndrome viral',
            'Faringoamigdalitis',
            'Resfriado común',
            'Dolencia muscular'
        ],
        'tratamientos': [
            'Paracetamol 500mg cada 6 horas por 3 días',
            'Reposo e hidratación abundante',
            'Omeprazol 20mg en ayunas por 7 días',
            'Vitamina B12 orale diaria',
            'Ibuprofeno 400mg cada 8 horas',
            'Amoxicilina 500mg cada 8 horas por 5 días',
            'Loratadina 10mg diaria por 5 días',
            'Dieta blanda y abundantes líquidos'
        ]
    },
    2: {  # Pediatría
        'sintomas': [
            'Fiebre en niño de 5 años',
            'Tos con producción mucosa',
            'Dolor de garganta en niño',
            'Erupción cutánea en tronco',
            'Vómitos postprandiales',
            'Diarrea líquida verde',
            'Llanto persistente del niño',
            'Falta de apetito'
        ],
        'diagnosticos': [
            'Infección respiratoria aguda',
            'Amigdalitis bacteriana aguda',
            'Gastroenteritis infantil',
            'Alergia alimentaria',
            'Varicela infantil',
            'Otitis media aguda',
            'Bronquiolitis',
            'Exantema viral'
        ],
        'tratamientos': [
            'Azitromicina 250mg diaria por 3 días',
            'Cetirizina gotas cada 24 horas',
            'Sulbutamol jarabe cada 6 horas',
            'Rehidratación oral con sales',
            'Nistatina suspensión oral',
            'Paracetamol infantilcada 6 horas',
            'Dieta blanda astringente',
            'Vitaminas infantiles diaria'
        ]
    },
    3: {  # Cardiología
        'sintomas': [
            'Dolor torácico tipo presiones',
            'Palpitaciones irregulares',
            'Disnea de esfuerzo',
            'Mareos al levantarse',
            'Edema en miembros inferiores',
            'Fatiga excesiva',
            'Aleteo cardiaco',
            'Síncope'
        ],
        'diagnosticos': [
            'Hipertensión arterial esencial',
            'Insuficiencia cardíaca congestiva',
            'Fibrilación auricular',
            'Cardiopatía isquémica crónica',
            'Angina de pecho estable',
            'Cardiomegalia',
            'Bradicardia sinusall',
            'Enfermedad arterial coronaria'
        ],
        'tratamientos': [
            'Losartan 50mg cada 24 horas',
            'Carvedilol 12.5mg cada 12 horas',
            'Enalapril 10mg cada 24 horas',
            'Amlodipino 5mg cada 24 horas',
            'Aspirina 100mg diaria',
            'Atorvastatina 20mg nocturna',
            'Furosemida 40mg cada 24 horas',
            'Dieta baja en sodio'
        ]
    },
    4: {  # Dermatología
        'sintomas': [
            'Erupción roja con prurito',
            'Manchas blancas en piel',
            'Acné facial con pus',
            'Lesión elevada en brazo',
            'Picazón intensa nocturna',
            'Uñas cambian de color',
            'Ampollas en las manos',
            'Enrojecimiento facial'
        ],
        'diagnosticos': [
            'Dermatitis atópica',
            'Psoriasis vulgar',
            'Acné grado II',
            'Onicomicosis',
            'Dermatitis por contacto',
            'Tiña corporal',
            'Herpes simple',
            'Urticaria aguda'
        ],
        'tratamientos': [
            'Hidrocortisona crema 1% aplicado',
            'Mometasona crema aplicado',
            'Clotrimazol crema aplicado',
            'Tretinoína crema aplicada',
            'Ciprofloxacino pomada',
            'Bencilo peroxide gel',
            'Antihistamínico oral',
            'Emoliente dermatológico'
        ]
    },
    5: {  # Ginecología
        'sintomas': [
            'Dolor pélvico menstrual',
            'Sangrado intermenstrual',
            'Flujo vaginal anormal',
            'Dolores ovulatorios',
            'Náuseas matutinas',
            'Sequedad vaginal',
            'Sofocos nocturnos',
            'Retraso menstrual'
        ],
        'diagnosticos': [
            'Dismenorrea primaria',
            'Embarazo primer trimestre',
            'Candidiasis vaginal',
            'Endometriosis',
            'Síndrome de ovario poliquístico',
            'Menopausia',
            'Amenorrea secundaria',
            'Prolapso uterino grado I'
        ],
        'tratamientos': [
            'Ácido fólico 5mg diario',
            'Progesterona 200mg vaginal',
            'Clotrimazol óvulos',
            'Antiespasmódico oral',
            'Hierro sulfato 300mg',
            'Estradiol parche',
            'Anticonceptivo combinado',
            'Suplemento de calcio'
        ]
    },
    6: {  # Traumatología
        'sintomas': [
            'Dolor de rodilla al caminar',
            'Dolor lumbar irradiado',
            'Tobillo hinchado post-lesión',
            'Hombro dificulta elevación',
            'Dolor articular mano',
            'Rigidez matutina articular',
            'Crujido al mover articulación',
            'Limitación de movimiento'
        ],
        'diagnosticos': [
            'Esguince de rodilla',
            'Lumbalgia crónica',
            'Esguince de tobillo grado II',
            'Capsulitis adhesiva',
            'Artrosis de cadera',
            'Condromalacia rotuliana',
            'Bursitis olecraneana',
            'Lesión del manguito rotador'
        ],
        'tratamientos': [
            'Diclofenaco gel aplicado',
            'Ketorolaco 30mg oral',
            'Glucosamina sulfato oracle',
            'Fisioterapia 3 veces por semana',
            'Meloxicam 15mg diaria',
            'Tizanidina 4mg cada 8 horas',
            'Calcium D3 diaria',
            'Reposo relativo 7 días'
        ]
    },
    7: {  # Oftalmología
        'sintomas': [
            'Ojos rojos al despertar',
            'Visión borrosa temporal',
            'Ojo seco conardor',
            'Secreción mucosa',
            'Dolor ocular profundo',
            'Fotofobia',
            'Ojo lloroso constante',
            'Halos alrededor de luces'
        ],
        'diagnosticos': [
            'Conjuntivitis alérgica',
            'Ojo seco crónico',
            'Blefaritis',
            'Úlcera corneal',
            'Glaucoma de ángulo abierto',
            'Catarata nuclear',
            'Retinopatía diabética',
            'Desprendimiento de vítreo'
        ],
        'tratamientos': [
            'Timolol 0.5% gotas',
            'Lágrimas artificiales cada 2 horas',
            'Tobramdex ungüento',
            'Olopatadina gotas',
            'Cromoglicato 2% gotas',
            'Moxifloxacino gotas',
            'Aciclovir ungüento',
            'Cirugía de catarata'
        ]
    },
    8: {  # Neurología
        'sintomas': [
            'Dolor de cabeza intenso unilateral',
            'Mareos con vértigo',
            'Pérdida de equilibrio',
            'Entumecimiento de extremidades',
            'Episodios deAusencia',
            'Dificultad para hablar',
            'Temblor en reposo',
            'Pérdida de memoria reciente'
        ],
        'diagnosticos': [
            'Migraña con aura',
            'Epilepsia focal',
            'Vértigoposicional benigno',
            'Neuropatía periférica',
            'Enfermedad de Parkinson',
            'ACV isquémico',
            'Síndrome del túnel del carpo',
            'Demencia vascular'
        ],
        'tratamientos': [
            'Rizatriptan 5mg al inicio de dolor',
            'Levetiracetam 500mg cada 12 horas',
            'Valproato 500mg cada 12 horas',
            'Pregabalina 75mg cada 12 horas',
            'Topiramato 50mg cada 12 horas',
            'Gabapentina 300mg cada 8 horas',
            'Amitriptilina 25mg al acostarse',
            'Oxcarbazepina 300mg cada 12 horas'
        ]
    },
    9: {  # Psiquiatría
        'sintomas': [
            'Tristeza persistente',
            'Ansiedad excesiva',
            'Insomnio de conciliación',
            'Aislamiento social',
            'Alucinaciones visuales',
            'Cambios de humor rápidos',
            'Fobias específicas',
            'Angustia panico'
        ],
        'diagnosticos': [
            'Episodio depresivo mayor',
            'Trastorno de ansiedad generalizada',
            'Insomnio primario',
            'Esquizofrenia paranoide',
            'Trastorno bipolar tipo I',
            'Fobia social',
            'Trastorno de pánico',
            'Estado de estrés postraumático'
        ],
        'tratamientos': [
            'Sertralina 50mg diaria',
            'Fluoxetina 20mg diaria',
            'Escitalopram 10mg diaria',
            'Quetiapina 25mg al acostarse',
            'Alprazolam 0.5mg cada 8 horas',
            'Risperidona 2mg cada 12 horas',
            'Lorazepam 1mg al acostarse',
            'Psicoterapia semanal'
        ]
    },
    10: {  # Otorrinolaringología
        'sintomas': [
            'Dolor de oído medio',
            'Nariz tapada persistente',
            'Dolor de garganta al tragar',
            'Sangrado nasal unilateral',
            'Pérdida auditiva parcial',
            'Zumbido en oídos',
            'Mareo con náuseas',
            'Voz ronca por 2 semanas'
        ],
        'diagnosticos': [
            'Otitis media serosa',
            'Rinosinusitis crónica',
            'Amigdalitis recurrente',
            'Epistaxis recidivante',
            'Sordera conductiva',
            'Acúfenos',
            'Enfermedad de Ménière',
            'Nódulos en cuerdas vocales'
        ],
        'tratamientos': [
            'Pseudofedrina 30mg cada 6 horas',
            'Xylometazolina nasal',
            'Amoxicilina clavulanato cada 12h',
            'Triamcinolona nasal diaria',
            'Mupirocina nasal',
            'Carbocisteína jarabe',
            'Beclometasona inhalador',
            'Reposo vocal 5 días'
        ]
    },
    11: {  # Urología
        'sintomas': [
            'Ardor al orinar',
            'Sangre en la orina',
            'Urgencia miccional',
            'Dificultad para orinar',
            'Goteo postmiccional',
            'Dolor prostático',
            'Incontinencia urinaria',
            'Pesadez pélvica'
        ],
        'diagnosticos': [
            'Infección urinaria baja',
            'Cálculo renal en uréter',
            'Hiperplasia prostática benigna',
            'Cistitis hemorrágica',
            'Prostatitis crónicas',
            'Incontinencia urinaria de esfuerzo',
            'Vejiga neurogénica',
            'Orchitis aguda'
        ],
        'tratamientos': [
            'Ciprofloxacino 500mg cada 12 horas',
            'Nitrofurantoína 100mg cada 6 horas',
            'Tamsulosina 0.4mg diaria',
            'Finasterida 5mg diaria',
            'Oxibutinina 5mg cada 8 horas',
            'Tolterodina 4mg diaria',
            'Fenazopiridina 100mg',
            'Baños de asientos'
        ]
    },
    12: {  # Endocrinología
        'sintomas': [
            'Sed excesiva',
            'Pérdida de peso sin causa',
            'Fatiga cronica',
            'Bocio palpable',
            'Intolerancia al frío',
            'Aumento de apetito',
            'Piel seca y粗糙',
            'Latido cardiaco lento'
        ],
        'diagnosticos': [
            'Diabetes mellitus tipo 2',
            'Hipotiroidismo subclínico',
            'Hipertiroidismo',
            'Obesidad grado II',
            'Síndrome metabólico',
            'Tiroiditis autoinmune',
            'Bocio nodular tóxico',
            'Déficit de vitamina D'
        ],
        'tratamientos': [
            'Metformina 850mg cada 12 horas',
            'Levotiroxina 100mcg en ayunas',
            'Glimepirida 4mg diaria',
            'Sitagliptina 100mg diaria',
            'Empagliflozina 10mg diaria',
            'Dieta hipocalórica',
            'Vitamina D3 2000UI diaria',
            'Ejercicio aeróbico diario'
        ]
    },
    13: {  # Neumología
        'sintomas': [
            'Tos persistente por 4 semanas',
            'Falta de aire al subir escaleras',
            'Silbidos en el pecho',
            'Dolor torácico pleurítico',
            'Expulsión de sangre',
            'Tos con flema verde',
            ' apnea nocturna',
            'Expectoración mucosa'
        ],
        'diagnosticos': [
            'Asma bronquial intermitente',
            'EPOC moderado',
            'Neumonía lobar',
            'Bronquiectasias',
            'Tuberculosis pulmonar',
            'Bronquitis crónica',
            'Neumotórax espontáneo',
            'Enfermedad intersticial'
        ],
        'tratamientos': [
            'Fluticasona 250mcg inhalador',
            'Salbutamol aerosol rescue',
            'Budesonida nebulización',
            'Montelukast 10mg nocturn',
            'Azitromicina 500mg diaria',
            'Doxoficilina 400mg cada 12 horas',
            'Oxygenoterapia nocturna',
            'Rehabilitación respiratoria'
        ]
    },
    14: {  # Gastroenterología
        'sintomas': [
            'Acidez retroesternal',
            'Dolor epigástrico',
            'Diarrea líquida',
            'Estreñimiento funcional',
            'Náuseas postprandiales',
            'Heces con sangre',
            'Distensión abdominal',
            'Saciedad temprana'
        ],
        'diagnosticos': [
            'Enfermedad por reflujo gastroesofágico',
            'Úlcera péptica duodenal',
            'Síndrome de intestino irritable',
            'Gastritis crónica H. pylori',
            'Colitis ulcerosa',
            'Enfermedad de Crohn',
            'Diverticulosis colónica',
            'Intolerancia a la lactosa'
        ],
        'tratamientos': [
            'Pantoprazol 40mg en ayunas',
            'Esomeprazol 20mg cada 12 horas',
            'Domperidona 10mg antes de comer',
            'Ondansetrón 8mg si náuseas',
            'Loperamida 2mg dopo evacuación',
            'Lactulosa jarabe',
            'Mesalazina 500mg cada 8 horas',
            'Dieta libre de gluten'
        ]
    },
    15: {  # Reumatología
        'sintomas': [
            'Dolor articular múltiples',
            'Rigidez matutina mayor 1 hora',
            'Hinchazón de manos',
            'Deformidad articular visible',
            'Fatiga muscular',
            'Fiebre baja vespertina',
            'Nódulos subcutáneos',
            'Dolor lumbar inflamatorio'
        ],
        'diagnosticos': [
            'Artritis reumatoide',
            'Osteoartritis generalizada',
            'Lupus eritematoso sistémico',
            'Gota úrica',
            'Fibromialgia',
            'Espondilitis anquilosante',
            'Polimialgia reumática',
            'Síndrome de Sjögren'
        ],
        'tratamientos': [
            'Metotrexate 15mg semanal',
            'Sulfasalazina 500mg cada 8 horas',
            'Hydroxychloroquine 200mg cada 12 horas',
            'Allopurinol 300mg nocturna',
            'Colchicina 0.5mg en crisis',
            'Leflunomida 20mg diaria',
            'Etanercept 50mg subcutáneo semanal',
            'Fisioterapia articular'
        ]
    },
    16: {  # Angiología
        'sintomas': [
            'Piernas hinchadas al final del día',
            'Venas varicosas visibles',
            'Dolor al caminar',
            'Úlcera en Tobillo',
            'Frialdad en extremidades',
            'Calambres nocturnos',
            'Pieloscurecida en piernas',
            'Claudicación intermitente'
        ],
        'diagnosticos': [
            'Insuficiencia venosa crónica',
            'Varicesprimarias bilaterales',
            'Trombosis venosa profunda',
            'Úlcera venosa activa',
            'Enfermedad arterial periférica',
            'Síndrome postrombótico',
            'Acrocianosis',
            'Linfedema secundario'
        ],
        'tratamientos': [
            'Diosmina 500mg cada 12 horas',
            'Pentoxifilina 400mg cada 8 horas',
            'Cilostazol 100mg cada 12 horas',
            'Aspirina 100mg diaria',
            'Rivaroxaban 20mg diaria',
            'Compresión elástica',
            'Elevación de piernas',
            'Cuidado de heridas'
        ]
    },
}

# Update all consultations to be specific to specialty
print("=== ACTUALIZANDO CONSULTAS ===")

for esp_id, esp_data in data.items():
    # Get all appointments for this specialty
    citas = conn.execute(
        "SELECT c.id, c.ticket FROM citas c WHERE c.id_especialidad = ?",
        (esp_id,)
    ).fetchall()

    for cita in citas:
        id_cita = cita[0]

        # Skip if already has good symptoms (not generic)
        existing = conn.execute(
            "SELECT sintomas FROM consultas WHERE id_cita = ?",
            (id_cita,)
        ).fetchone()

        if existing and len(existing[0]) > 25:  # Has meaningful symptoms
            continue

        # Generate new specific data
        sintomas = random.choice(esp_data['sintomas'])
        diagnostico = random.choice(esp_data['diagnosticos'])
        tratamiento = random.choice(esp_data['tratamientos'])

        conn.execute(
            "UPDATE consultas SET sintomas = ?, diagnostico = ?, tratamiento = ? WHERE id_cita = ?",
            (sintomas, diagnostico, tratamiento, id_cita)
        )

    print(f"Especialidad {esp_id}: {len(citas)} citas actualizadas")

conn.commit()

# Verify
print("\n=== VERIFICACIÓN ===")
for esp_id in range(1, 17):
    esp = conn.execute("SELECT nombre FROM especialidades WHERE id = ?", (esp_id,)).fetchone()
    sample = conn.execute('''
        SELECT c.diagnostico, c.sintomas
        FROM consultas c
        JOIN citas ct ON c.id_cita = ct.id
        WHERE ct.id_especialidad = ?
        LIMIT 2
    ''', (esp_id,)).fetchall()
    print(f"\n{esp[0]}:")
    for s in sample:
        print(f"  Dx: {s[0][:35]}...")
        print(f"  Sx: {s[1][:35]}...")

conn.close()
print("\n¡Completado!")
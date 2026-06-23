import sqlite3

conn = sqlite3.connect('clinic_app.sqlite3')

# medicamentos por especialidad: (nombre, descripcion, precio, stock)
medicamentos = [
    # Medicina General
    ('Paracetamol 500 mg', 'Analgésico y antipirético', 0.50, 200),
    ('Ibuprofeno 400 mg', 'Antiinflamatorio no esteroideo', 0.80, 150),
    ('Amoxicilina 500 mg', 'Antibiótico de amplio espectro', 1.20, 100),
    ('Loratadina 10 mg', 'Antihistamónico', 0.60, 120),
    ('Omeprazol 20 mg', 'Inhibidor de bomba de protones', 0.90, 80),
    ('Metformina 500 mg', 'Antidiabético oral', 1.00, 90),
    ('Losartan 50 mg', 'Antihipertensivo', 1.10, 85),
    ('Aspirina 100 mg', 'Antiagregante plaquetario', 0.70, 100),

    # Pediatría
    ('Azitromicina 250 mg', 'Antibiótico pediátrico', 1.50, 80),
    ('Cetirizina 5 mg', 'Antihistamónico pediátrico', 0.80, 90),
    ('Sulbutamol 2 mg', 'Broncodilatador pediátrico', 1.00, 70),
    ('Nistatina suspensión', 'Antifúngico oral', 1.30, 50),
    ('Sales rehidratación ORS', 'Sales de rehidratación oral', 0.40, 150),
    ('Vitaminas infantiles', 'Suplemento vitamínico', 1.20, 60),
    ('Ibuprofeno suspensión', 'Analgésico pediátrico', 1.00, 80),

    # Cardiología
    ('Atorvastatina 20 mg', 'Estatina para colesterol', 2.50, 60),
    ('Carvedilol 12.5 mg', 'Betabloqueador', 2.00, 50),
    ('Enalapril 10 mg', 'IECAn', 1.80, 55),
    ('Amlodipino 5 mg', 'Bloqueador cálcico', 1.60, 60),
    ('Digoxina 0.25 mg', 'Glucósido cardíaco', 2.20, 40),
    ('Furosemida 40 mg', 'Diurético', 0.90, 70),
    ('Clopidogrel 75 mg', 'Antiplaquetario', 2.80, 50),
    ('Warfarina 5 mg', 'Anticoagulante', 1.90, 45),

    # Dermatología
    ('Clotrimazol crema 1%', 'Antifúngico tópico', 2.00, 80),
    ('Hidrocortisona 1%', 'Corticosteroide tópico', 1.50, 90),
    ('Mometasona crema', 'Corticosteroide potente', 3.50, 60),
    ('Benzoyl peroxide 5%', 'Peróxido antibacteriano', 2.20, 70),
    ('Tretinoína 0.025%', 'Retinoide tópico', 4.00, 40),
    ('Ciprofloxacino crema', 'Antibiótico tópico', 2.50, 55),
    ('Clindamicina solución', 'Antibiótico para acne', 2.80, 50),
    ('Tacrolimus 0.1%', 'Inmunosupresor tópico', 5.00, 30),

    # Ginecología
    ('Levonorgestrel 1.5 mg', 'Anticonceptivo de emergencia', 3.00, 50),
    ('Progesterona 200 mg', 'Suplemento hormonal', 2.50, 60),
    ('Ácido fólico 5 mg', 'Suplemento prenatal', 0.50, 200),
    ('Hierro sulfato 300 mg', 'Suplemento de hierro', 0.60, 150),
    ('Estradiol crema', 'Estrógeno tópico', 3.50, 45),
    ('Metronidazol óvulos', 'Antiprotozoario vaginal', 2.00, 60),
    ('Clotrimazol óvulos', 'Antifúngico vaginal', 2.20, 70),
    ('Dinoproston gel', 'Inductor del parto', 4.50, 25),

    # Traumatología
    ('Diclofenaco gel', 'Antiinflamatorio tópico', 2.50, 80),
    ('Ketorolaco 30 mg', 'Analgésico potente', 2.00, 60),
    ('Tramadol 50 mg', 'Analgésico opioide', 1.80, 55),
    ('Gabapentina 300 mg', 'Anticonvulsivante', 2.20, 70),
    ('Calcium D3', 'Suplemento calcio', 1.50, 100),
    ('Glucosamina sulfato', 'Condoprotector', 2.80, 60),
    ('Meloxicam 15 mg', 'AINEs selectivo', 2.10, 50),
    ('Tizanidina 4 mg', 'Relajante muscular', 1.90, 45),

    # Oftalmología
    ('Timolol 0.5%', 'Betabloqueador ocular', 3.00, 40),
    ('Lágrimas artificiales', 'Lubricante ocular', 2.50, 80),
    ('Tobramdex gotas', 'Antibiótico esteroideo ocular', 4.00, 35),
    ('Cromoglicato 2%', 'Antiinflamatorio ocular', 3.20, 45),
    ('Moxifloxacino gotas', 'Antibiótico ocular', 3.80, 40),
    ('Fluorometolona gotas', 'Corticosteroide ocular', 3.50, 35),
    ('Olopatadina gotas', 'Antihistamónico ocular', 3.00, 50),
    ('Aciclovir ungüento 3%', 'Antiviral ocular', 4.50, 30),

    # Neurología
    ('Levetiracetam 500 mg', 'Anticonvulsivante', 3.50, 60),
    ('Valproato 500 mg', 'Estabilizador ánimo', 2.80, 55),
    ('Pregabalina 75 mg', 'Anticonvulsivante', 3.20, 50),
    ('Rizatriptan 5 mg', 'Triptán para migraña', 4.00, 40),
    ('Sumatriptan 50 mg', 'Triptán migrana', 3.80, 45),
    ('Topiramato 50 mg', 'Anticonvulsivante', 2.90, 55),
    ('Amitriptilina 25 mg', 'Antidepresivo tricíclico', 1.00, 70),
    ('Oxcarbazepina 300 mg', 'Anticonvulsivante', 3.00, 50),

    # Psiquiatría
    ('Sertralina 50 mg', 'ISRS antidepresivo', 2.50, 70),
    ('Fluoxetina 20 mg', 'ISRS antidepresivo', 2.00, 80),
    ('Escitalopram 10 mg', 'ISRS selectivo', 2.80, 60),
    ('Quetiapina 25 mg', 'Antipsicótico', 3.50, 50),
    ('Risperidona 2 mg', 'Antipsicótico', 2.80, 55),
    ('Alprazolam 0.5 mg', 'Benzodiazepina', 1.00, 90),
    ('Lorazepam 1 mg', 'Benzodiazepina', 0.90, 85),
    ('Mianserina 30 mg', 'Antidepresivo tetracíclico', 2.20, 50),

    # Otorrinolaringología
    ('Pseudofedrina 30 mg', 'Descongestivo nasal', 1.00, 100),
    ('Xylometazolina gotas', 'Descongestivo nasal', 1.50, 80),
    ('Triamcinolona nasal', 'Corticosteroide nasal', 2.50, 60),
    ('Amoxicilina clavulanato', 'Antibiótico amplio', 2.20, 70),
    ('Mupirocina ungüento', 'Antibiótico nasal', 3.00, 45),
    ('Ipratropio aerosol', 'Broncodilatador', 2.80, 50),
    ('Carbocisteína jarabe', 'Mucolítico', 1.80, 65),
    ('Beclometasona nasal', 'Corticosteroide nasal', 2.80, 55),

    # Urología
    ('Tamsulosina 0.4 mg', 'Alfabloqueador', 2.50, 55),
    ('Finasterida 5 mg', 'Inhibidor 5-alfa', 2.80, 50),
    ('Oxibutinina 5 mg', 'Anticolinérgico', 2.20, 45),
    ('Tolterodina 4 mg', 'Anticolinérgico', 2.50, 40),
    ('Ciprofloxacino 500 mg', 'Antibiótico quinolona', 1.50, 80),
    ('Nitrofurantoína 100 mg', 'Antibiótico urinario', 2.00, 60),
    ('Fenazopiridina 100 mg', 'Analgésico urinario', 1.80, 50),
    ('Tamsulosina dutasterida', 'Combinación anti-ADP', 4.00, 35),

    # Endocrinología
    ('Levotiroxina 100 mcg', 'Hormona tiroidea', 1.00, 150),
    ('Metformina 850 mg', 'Biguanida', 1.20, 100),
    ('Glimepirida 4 mg', 'Sulfonilurea', 2.00, 60),
    ('Sitagliptina 100 mg', 'DPP-4 inhibidor', 3.50, 50),
    ('Empagliflozina 10 mg', 'SGLT2 inhibidor', 4.00, 45),
    ('Insulina glargina', 'Análogo insulina', 5.00, 30),
    ('Prednisona 5 mg', 'Corticosteroide', 0.80, 100),
    ('Hidrocortisona 20 mg', 'Corticosteroide', 1.00, 70),

    # Neumología
    ('Fluticasona aerosol', 'Corticosteroide inhalado', 4.00, 50),
    ('Salbutamol inhaler', 'Broncodilatador', 3.00, 80),
    ('Budesonida nebulización', 'Corticosteroide', 3.50, 50),
    ('Montelukast 10 mg', 'Leucotrieno antagonista', 3.20, 60),
    ('Azitromicina 500 mg', 'Macrólido', 2.00, 70),
    ('Doxoficilina 400 mg', 'Broncodilatador', 2.50, 55),
    ('Roflumil crema', 'Fosfodiesterasa inhibidor', 4.50, 35),
    ('Cromo Sodico inhalador', 'Estabilizador mastocito', 3.80, 40),

    # Gastroenterología
    ('Pantoprazol 40 mg', 'Bomba protones inhib', 1.80, 100),
    ('Esomeprazol 20 mg', 'Bomba protones inhib', 2.20, 80),
    ('Domperidona 10 mg', 'Antiemético', 1.50, 70),
    ('Ondansetrón 8 mg', 'Antiemético', 2.80, 60),
    ('Loperamida 2 mg', 'Antidiarreico', 1.00, 90),
    ('Racecadotrilo 100 mg', 'Antisecretorio', 2.50, 55),
    ('Mesalazina 500 mg', 'Antiinflamatorio intestinal', 3.00, 50),
    ('Lactulosa jarabe', 'Laxante osmótico', 1.50, 70),

    # Reumatología
    ('Etanercept 50 mg', 'Biológico anti-TNF', 8.00, 20),
    ('Adalimumab 40 mg', 'Biológico anti-TNF', 9.00, 15),
    ('Metotrexate 15 mg', 'Inmunosupresor', 3.50, 40),
    ('Sulfasalazina 500 mg', 'DMARD', 2.80, 50),
    ('Hydroxychloroquine 200 mg', 'Antimalárico', 2.00, 60),
    ('Colchicina 0.5 mg', 'Antigotoso', 2.20, 55),
    ('Allopurinol 300 mg', 'Antigotoso', 1.50, 70),
    ('Leflunomida 20 mg', 'DMARD', 4.50, 35),

    # Angiología
    ('Pentoxifilina 400 mg', 'Vasodilatador', 2.50, 60),
    ('Cilostazol 100 mg', 'Antiplaquetario', 3.80, 45),
    ('Diosmina 500 mg', 'Venotónico', 2.80, 70),
    ('Aspirina protect', 'Antiplaquetario', 1.00, 100),
    ('Rivaroxaban 20 mg', 'Anticoagulante', 4.50, 35),
    ('Apixaban 5 mg', 'Anticoagulante', 4.80, 30),
    ('Dabigatran 150 mg', 'Anticoagulante', 4.20, 35),
    ('Enoxaparina 40 mg', 'Heparina de bajo peso', 3.50, 40),
]

print('=== AGREGANDO MEDICAMENTOS ===')
for i, med in enumerate(medicamentos):
    nombre, desc, precio, stock = med
    try:
        conn.execute('''
            INSERT INTO medicamentos (nombre, descripcion, precio, stock, activo, fecha_creacion)
            VALUES (?, ?, ?, ?, 1, datetime('now'))
        ''', (nombre, desc, precio, stock))
        if (i + 1) % 8 == 0:
            print(f'{i+1}. {nombre} - OK')
    except Exception as e:
        print(f'Error {nombre}: {e}')

conn.commit()
print(f'Total medicamentos agregados: {len(medicamentos)}')
conn.close()
print('Medicamentos guardados correctamente!')
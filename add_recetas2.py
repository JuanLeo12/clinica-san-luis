import sqlite3
import random

conn = sqlite3.connect('clinic_app.sqlite3')

data = {
    1: ['Paracetamol 500 mg', 'Ibuprofeno 400 mg', 'Amoxicilina 500 mg'],
    2: ['Azitromicina 250 mg', 'Cetirizina 5 mg', 'Sulbutamol 2 mg'],
    3: ['Atorvastatina 20 mg', 'Carvedilol 12.5 mg', 'Enalapril 10 mg'],
    4: ['Clotrimazol crema 1%', 'Hidrocortisona 1%', 'Mometasona crema'],
    5: ['Levonorgestrel 1.5 mg', 'Progesterona 200 mg', 'Acido folico 5 mg'],
    6: ['Diclofenaco gel', 'Ketorolaco 30 mg', 'Glucosamina sulfato'],
    7: ['Timolol 0.5%', 'Lagrimas artificiales', 'Tobramdex gotas'],
    8: ['Rizatriptan 5 mg', 'Levetiracetam 500 mg', 'Valproato 500 mg'],
    9: ['Sertralina 50 mg', 'Fluoxetina 20 mg', 'Escitalopram 10 mg'],
    10: ['Pseudofedrina 30 mg', 'Xylometazolina gotas', 'Amoxicilina clavulanato'],
    11: ['Tamsulosina 0.4 mg', 'Finasterida 5 mg', 'Ciprofloxacino 500 mg'],
    12: ['Levotiroxina 100 mcg', 'Metformina 850 mg', 'Glimepirida 4 mg'],
    13: ['Fluticasona aerosol', 'Salbutamol inhaler', 'Montelukast 10 mg'],
    14: ['Pantoprazol 40 mg', 'Esomeprazol 20 mg', 'Loperamida 2 mg'],
    15: ['Metotrexate 15 mg', 'Sulfasalazina 500 mg', 'Allopurinol 300 mg'],
    16: ['Pentoxifilina 400 mg', 'Cilostazol 100 mg', 'Diosmina 500 mg'],
}

citas = conn.execute(
    "SELECT c.id, c.id_especialidad, c.ticket, con.id FROM citas c "
    "JOIN consultas con ON con.id_cita = c.id "
    "WHERE c.id NOT IN (SELECT id_cita FROM recetas) ORDER BY c.id LIMIT 100"
).fetchall()

print(f"Citas sin receta: {len(citas)}")
creadas = 0

for cita in citas:
    try:
        id_cita = cita[0]
        id_consulta = cita[3]
        id_esp = cita[1]

        meds = data.get(id_esp, data[1])
        meds_sample = random.sample(meds, 3)

        total = round(random.uniform(20, 120), 2)
        conn.execute(
            "INSERT INTO recetas (id_cita, id_consulta, estado, total, fecha_creacion) "
            "VALUES (?, ?, 'dispensado', ?, datetime('now'))",
            (id_cita, id_consulta, total)
        )

        id_receta = conn.execute("SELECT last_insert_rowid()").fetchone()[0]

        for med in meds_sample:
            conn.execute(
                "INSERT INTO receta_items (id_receta, medicina, dosis, frecuencia, dias, cantidad, precio_unitario) "
                "VALUES (?, ?, '1 comprimido', 'Cada 8 horas', ?, ?, ?)",
                (id_receta, med, random.randint(5, 10), random.randint(1, 3), round(random.uniform(1, 5), 2))
            )

        creadas += 1
    except Exception as e:
        print(f"Error {cita[2]}: {e}")

conn.commit()
print(f"Creadas: {creadas}")

recetas = conn.execute("SELECT COUNT(*) FROM recetas").fetchone()[0]
items = conn.execute("SELECT COUNT(*) FROM receta_items").fetchone()[0]
print(f"Recetas: {recetas}, Items: {items}")
conn.close()
print("Listo!")
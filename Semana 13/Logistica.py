import tkinter as tk
from tkinter import ttk, messagebox
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split

# Cargar los datos desde el archivo Excel
file_path = 'LogisticaBase.xlsx'  # Ruta del archivo Excel
data = pd.read_excel(file_path)

# Preparar los datos
X = data[['Meses', 'Promedio de horas semanales']]
y = data['Requerimiento']

X_entrenamiento, X_prueba, y_entrenamiento, y_prueba = train_test_split(
    X, y,
    test_size=0.2,
    random_state=42
)

model = LogisticRegression()
model.fit(X_entrenamiento, y_entrenamiento)

# Función para predecir la probabilidad de que una máquina sea requerida
def predecir_probabilidad():
    try:
        meses = float(entry_meses.get())
        horas = float(entry_horas.get())

        # Realizar la predicción
        probabilidad = model.predict_proba([[meses, horas]])[0][1]

        # Mostrar la probabilidad
        label_probabilidad.config(
            text=f"Probabilidad: {probabilidad:.4f}"
        )

        # Guardar los resultados en el Treeview
        tree.insert(
            '',
            'end',
            values=(meses, horas, f"{probabilidad:.4f}")
        )

    except ValueError:
        messagebox.showerror(
            "Error",
            "Por favor ingrese valores numéricos válidos para meses y horas."
        )


# Función para exportar los datos del Treeview a Excel
def exportar_excel():

    # Obtener los datos del Treeview
    tree_data = []

    for row in tree.get_children():
        tree_data.append(tree.item(row)['values'])

    # Crear un DataFrame de pandas
    df = pd.DataFrame(
        tree_data,
        columns=[
            "Meses",
            "Promedio de horas semanales",
            "Probabilidad"
        ]
    )

    # Exportar a un archivo Excel
    df.to_excel(
        'resultados_predicciones.xlsx',
        index=False
    )

    messagebox.showinfo(
        "Exportar",
        "Datos exportados exitosamente a 'resultados_predicciones.xlsx'."
    )

# Crear la ventana principal de Tkinter
root = tk.Tk()
root.title("Predicción de Probabilidad - Regresión Logística")

# Etiquetas y entradas para las variables de entrada
tk.Label(root, text="Meses:").grid(
    row=0,
    column=0,
    padx=10,
    pady=5
)

entry_meses = tk.Entry(root)
entry_meses.grid(
    row=0,
    column=1,
    padx=10,
    pady=5
)

tk.Label(
    root,
    text="Promedio de horas semanales:"
).grid(
    row=1,
    column=0,
    padx=10,
    pady=5
)

entry_horas = tk.Entry(root)
entry_horas.grid(
    row=1,
    column=1,
    padx=10,
    pady=5
)

# Botón para predecir la probabilidad
btn_predecir = tk.Button(
    root,
    text="Predecir Probabilidad",
    command=predecir_probabilidad
)

btn_predecir.grid(
    row=2,
    column=0,
    columnspan=2,
    pady=10
)

# Etiqueta para mostrar la probabilidad
label_probabilidad = tk.Label(
    root,
    text="Probabilidad: "
)

label_probabilidad.grid(
    row=3,
    column=0,
    columnspan=2,
    pady=5
)

# Crear el Treeview para mostrar los resultados
tree = ttk.Treeview(
    root,
    columns=("Meses", "Horas", "Probabilidad"),
    show="headings"
)

tree.heading("Meses", text="Meses")
tree.heading(
    "Horas",
    text="Promedio de horas semanales"
)
tree.heading(
    "Probabilidad",
    text="Probabilidad"
)

tree.grid(
    row=4,
    column=0,
    columnspan=2,
    pady=10
)

# Botón para exportar los datos a Excel
btn_exportar = tk.Button(
    root,
    text="Exportar a Excel",
    command=exportar_excel
)

btn_exportar.grid(
    row=5,
    column=0,
    columnspan=2,
    pady=10
)

# Ejecutar la interfaz gráfica
root.mainloop()
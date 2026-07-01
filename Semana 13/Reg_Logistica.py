import tkinter as tk
from tkinter import ttk, messagebox
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
import numpy as np

# Cargar los datos desde el archivo Excel
file_path = 'LogisticaBase.xlsx' # Ruta del archivo Excel
data = pd.read_excel(file_path)

# Preparar los datos
X = data[['Meses', 'Promedio de horas semanales']]
y = data['Requerimiento']

# Obtener los valores mínimos y máximos de X1 (Meses) y X2 (Horas semanales)
min_meses = X['Meses'].min()
max_meses = X['Meses'].max()
min_horas = X['Promedio de horas semanales'].min()
max_horas = X['Promedio de horas semanales'].max()

# Generar 1000 datos aleatorios dentro del rango de los datos existentes
np.random.seed(42)  # Para reproducibilidad
X_random = np.random.uniform(low=[min_meses, min_horas], high=[max_meses, max_horas], size=(1000, 2))
y_random = np.random.choice([0, 1], size=1000)  # Asumimos una distribución aleatoria para Y (0 o 1)

# Dividir los datos generados aleatoriamente en entrenamiento (80%) y prueba (20%)
X_train, X_test, y_train, y_test = train_test_split(X_random, y_random, test_size=0.2, random_state=42)

# Crear y entrenar el modelo de regresión logística
model = LogisticRegression()
model.fit(X_train, y_train)

# Función para predecir la probabilidad de que una máquina sea requerida
def predecir_probabilidad():
    try:
        # Generar una nueva semilla aleatoria para asegurar resultados diferentes
        np.random.seed() # Cambiar la semilla cada vez para resultados diferentes

        # Generar un nuevo valor aleatorio para la predicción en el conjunto de entrenamiento
        random_train_input = np.random.uniform(low=[min_meses, min_horas], high=[max_meses, max_horas], size=(1, 2))

        # Generar un nuevo valor aleatorio para la predicción en el conjunto de prueba
        random_test_input = np.random.uniform(low=[min_meses, min_horas], high=[max_meses, max_horas], size=(1, 2))

        # Mostrar los valores aleatorios generados en los cuadros de texto
        entry_meses.delete(0, tk.END)
        entry_meses.insert(0, f"{random_test_input[0][0]:.2f}")  # Muestra el valor de prueba en el cuadro de texto
        entry_horas.delete(0, tk.END)
        entry_horas.insert(0, f"{random_test_input[0][1]:.2f}")  # Muestra el valor de prueba en el cuadro de texto

        # Realizar la predicción para los datos de prueba (X_test) y los de entrenamiento (X_train)
        probabilidad_test = model.predict_proba(random_test_input)[0][1]  # Predicción sobre el primer dato del conjunto de prueba
        probabilidad_train = model.predict_proba(random_train_input)[0][1] # Predicción sobre el primer dato del conjunto de entrenamiento

        # Comparar las probabilidades para ver si la diferencia es significativa
        diferencia = abs(probabilidad_train - probabilidad_test)
        if diferencia > 0.05:  # Umbral de diferencia significativa
            diferencia_significativa = 1
        else:
            diferencia_significativa = 0

        label_probabilidad_test.config(text=f"Probabilidad (Test): {probabilidad_test:.2f}")
        label_probabilidad_train.config(text=f"Probabilidad (Train): {probabilidad_train:.2f}")
        label_diferencia.config(text=f"Diferencia Significativa: {diferencia_significativa}")

        # Guardar los resultados en el Treeview con 2 decimales
        tree.insert('', 'end', values=(f"{random_test_input[0][0]:.2f}", f"{random_test_input[0][1]:.2f}",
                                       f"{probabilidad_test:.2f}", f"{probabilidad_train:.2f}", diferencia_significativa))

    except ValueError:
        messagebox.showerror("Error", "Por favor ingrese valores numéricos válidos para meses y horas.")

# Función para exportar los datos del Treeview a Excel
def exportar_excel():
    # Obtener los datos del Treeview
    tree_data = []
    for row in tree.get_children():
        tree_data.append(tree.item(row)['values'])

    # Crear un DataFrame de pandas
    df = pd.DataFrame(tree_data, columns=["Meses", "Promedio de horas semanales",
                                          "Probabilidad Test", "Probabilidad Train", "Diferencia Significativa"])

    # Exportar a un archivo Excel
    df.to_excel('resultados_predicciones_comparativas_generadas.xlsx', index=False)
    messagebox.showinfo("Exportar", "Datos exportados exitosamente a 'resultados_predicciones_comparativas_generadas.xlsx'.")

# Crear la ventana principal de Tkinter
root = tk.Tk()
root.title("Predicción de Probabilidad - Regresión Logística")

# Crear las etiquetas y entradas (entry) para Meses y Horas
tk.Label(root, text="Meses:").grid(row=0, column=0, padx=10, pady=5)
entry_meses = tk.Entry(root)
entry_meses.grid(row=0, column=1, padx=10, pady=5)

tk.Label(root, text="Promedio de horas semanales:").grid(row=1, column=0, padx=10, pady=5)
entry_horas = tk.Entry(root)
entry_horas.grid(row=1, column=1, padx=10, pady=5)

# Botón para predecir la probabilidad
btn_predecir = tk.Button(root, text="Predecir Probabilidad", command=predecir_probabilidad)
btn_predecir.grid(row=2, column=0, columnspan=2, pady=10)

# Crear las etiquetas para mostrar las probabilidades y la diferencia
label_probabilidad_test = tk.Label(root, text="Probabilidad (Test): ")
label_probabilidad_test.grid(row=3, column=0, columnspan=2, pady=5)

label_probabilidad_train = tk.Label(root, text="Probabilidad (Train): ")
label_probabilidad_train.grid(row=4, column=0, columnspan=2, pady=5)

label_diferencia = tk.Label(root, text="Diferencia Significativa: ")
label_diferencia.grid(row=5, column=0, columnspan=2, pady=5)

# Crear el Treeview para mostrar los resultados
tree = ttk.Treeview(root, columns=("Meses", "Horas", "Probabilidad Test", "Probabilidad Train", "Diferencia Significativa"), show="headings")
tree.heading("Meses", text="Meses")
tree.heading("Horas", text="Promedio de horas semanales")
tree.heading("Probabilidad Test", text="Probabilidad Test")
tree.heading("Probabilidad Train", text="Probabilidad Train")
tree.heading("Diferencia Significativa", text="Diferencia Significativa")

tree.grid(row=6, column=0, columnspan=2, pady=10)

# Botón para exportar los datos a Excel
btn_exportar = tk.Button(root, text="Exportar a Excel", command=exportar_excel)
btn_exportar.grid(row=7, column=0, columnspan=2, pady=10)

# Ejecutar la interfaz gráfica
root.mainloop()
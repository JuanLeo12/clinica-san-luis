import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.model_selection import cross_val_score
from sklearn.preprocessing import LabelEncoder
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    classification_report,
    confusion_matrix
)
import matplotlib.pyplot as plt
import numpy as np
from sklearn.tree import plot_tree
from sklearn.metrics import ConfusionMatrixDisplay
from sklearn.metrics import RocCurveDisplay
from sklearn.metrics import roc_curve
from sklearn.metrics import auc

# ==========================
# VARIABLES GLOBALES
# ==========================

df = None
modelo_entrenado = None

X_test_global = None
y_test_global = None

accuracy_global = 0

algoritmo_actual = ""

# ==========================
# FUNCION ABRIR ARCHIVO
# ==========================

def abrir_excel():

    global df

    archivo = filedialog.askopenfilename(
        title="Seleccionar Excel",
        filetypes=[("Excel", "*.xlsx *.xls")]
    )

    if archivo == "":
        return

    try:

        df = pd.read_excel(archivo)

        cargar_treeview()
        cargar_variables()

        lbl_archivo.config(text=archivo)

        messagebox.showinfo(
            "Correcto",
            "Archivo cargado correctamente"
        )

    except Exception as e:

        messagebox.showerror(
            "Error",
            str(e)
        )

# ==========================
# TREEVIEW
# ==========================

def cargar_treeview():

    for item in tree.get_children():
        tree.delete(item)

    tree["columns"] = list(df.columns)

    tree["show"] = "headings"

    for col in df.columns:

        tree.heading(col, text=col)
        tree.column(col, width=120)

    for fila in df.values.tolist():

        tree.insert(
            "",
            tk.END,
            values=fila
        )

# ==========================
# VARIABLES
# ==========================

def cargar_variables():

    listbox_x.delete(0, tk.END)

    combo_y["values"] = list(df.columns)

    for col in df.columns:

        listbox_x.insert(
            tk.END,
            col
        )

#OBTENER VARIABLES SELECCIONADAS
#================================
def obtener_variables_x():

    variables = []

    for indice in listbox_x.curselection():

        variables.append(
            listbox_x.get(indice)
        )

    return variables
# ==========================
# MOSTRAR SELECCION
# ==========================

def mostrar_configuracion():

    seleccion_x = []

    for indice in listbox_x.curselection():

        seleccion_x.append(
            listbox_x.get(indice)
        )

    variable_y = combo_y.get()

    algoritmo = algoritmo_var.get()

    texto = ""

    texto += "Variables X:\n"

    for x in seleccion_x:

        texto += f"{x}\n"

    texto += "\n"

    texto += f"Variable Y: {variable_y}\n"

    texto += f"Algoritmo: {algoritmo}\n"

    txt_resultados.delete(
        "1.0",
        tk.END
    )

    txt_resultados.insert(
        tk.END,
        texto
    )

def preparar_datos():

    global df

    variables_x = obtener_variables_x()

    variable_y = combo_y.get()

    if len(variables_x) < 2:

        messagebox.showwarning(
            "Advertencia",
            "Seleccione mínimo 2 variables predictoras"
        )

        return None

    if variable_y == "":

        messagebox.showwarning(
            "Advertencia",
            "Seleccione variable objetivo"
        )

        return None

    datos = df.copy()

    columnas = variables_x + [variable_y]

    datos = datos[columnas]

    datos = pd.get_dummies(datos)

    y_columnas = [

        c for c in datos.columns

        if c.startswith(variable_y)

    ]

    if len(y_columnas) > 0:

        y = datos[y_columnas[-1]]

        X = datos.drop(
            columns=y_columnas
        )

    else:

        X = datos.drop(
            columns=[variable_y]
        )

        y = datos[variable_y]

    return X, y

def mostrar_metricas(y_real, y_pred):

    accuracy = accuracy_score(
        y_real,
        y_pred
    )

    precision = precision_score(
        y_real,
        y_pred
    )

    recall = recall_score(
        y_real,
        y_pred
    )

    f1 = f1_score(
        y_real,
        y_pred
    )

    reporte = classification_report(
        y_real,
        y_pred
    )

    texto = ""

    texto += f"Accuracy : {accuracy:.4f}\n"
    texto += f"Precision: {precision:.4f}\n"
    texto += f"Recall   : {recall:.4f}\n"
    texto += f"F1 Score : {f1:.4f}\n\n"

    texto += "CLASSIFICATION REPORT\n\n"

    texto += reporte

    txt_resultados.delete(
        "1.0",
        tk.END
    )

    txt_resultados.insert(
        tk.END,
        texto
    )

    return accuracy

def entrenar_modelo():

    global modelo_entrenado
    global X_test_global
    global y_test_global
    global accuracy_global
    global algoritmo_actual

    resultado = preparar_datos()

    if resultado is None:
        return

    X, y = resultado

    X_train, X_test, y_train, y_test = train_test_split(

        X,
        y,

        test_size=0.20,

        random_state=42

    )

    algoritmo = algoritmo_var.get()

    if algoritmo == "Arbol":

        modelo = DecisionTreeClassifier(

            random_state=42,
            max_depth=4

        )

        algoritmo_actual = "Arbol"

    elif algoritmo == "Forest":

        modelo = RandomForestClassifier(

            n_estimators=100,

            random_state=42

        )

        algoritmo_actual = "Forest"

    else:

        modelo = LogisticRegression(

            max_iter=1000

        )

        algoritmo_actual = "Logistica"

    modelo.fit(

        X_train,
        y_train

    )

    y_pred = modelo.predict(
        X_test
    )

    accuracy_global = mostrar_metricas(

        y_test,
        y_pred

    )

    modelo_entrenado = modelo

    X_test_global = X_test

    y_test_global = y_test

    messagebox.showinfo(
        "Entrenamiento",
        "Modelo entrenado correctamente"
    )

def comparar_algoritmos():

    resultado = preparar_datos()

    if resultado is None:
        return

    X, y = resultado

    modelos = {

        "Arbol":
        DecisionTreeClassifier(),

        "Random Forest":
        RandomForestClassifier(),

        "Logistica":
        LogisticRegression(max_iter=1000)

    }

    nombres = []
    resultados = []

    texto = ""

    for nombre, modelo in modelos.items():

        scores = cross_val_score(

            modelo,

            X,

            y,

            cv=5,

            scoring="accuracy"

        )

        promedio = scores.mean()

        nombres.append(nombre)

        resultados.append(promedio)

        texto += f"{nombre}: {promedio:.4f}\n"

    txt_resultados.delete(
        "1.0",
        tk.END
    )

    txt_resultados.insert(
        tk.END,
        texto
    )

    plt.figure(figsize=(8,5))

    plt.bar(
        nombres,
        resultados
    )

    plt.title(
        "Comparación de Algoritmos"
    )

    plt.ylabel(
        "Accuracy"
    )

    plt.show()

def mostrar_graficos():

    global modelo_entrenado
    global algoritmo_actual
    global X_test_global
    global y_test_global

    if modelo_entrenado is None:

        messagebox.showwarning(
            "Advertencia",
            "Primero entrene un modelo"
        )

        return

    y_pred = modelo_entrenado.predict(
        X_test_global
    )

    matriz = confusion_matrix(
        y_test_global,
        y_pred
    )

    # MATRIZ DE CONFUSION

    fig, ax = plt.subplots(
        figsize=(6,5)
    )

    disp = ConfusionMatrixDisplay(
        confusion_matrix=matriz
    )

    disp.plot(ax=ax)

    ax.set_title(
        "Matriz de Confusión"
    )

    plt.show()

    # ARBOL

    if algoritmo_actual == "Arbol":

        plt.figure(figsize=(15,8))

        plot_tree(

            modelo_entrenado,

            filled=True,

            rounded=True,

            fontsize=8

        )

        plt.title(
            "Árbol de Decisión"
        )

        plt.show()

    # RANDOM FOREST

    elif algoritmo_actual == "Forest":

        importancias = modelo_entrenado.feature_importances_

        columnas = list(
            X_test_global.columns
        )

        plt.figure(figsize=(10,5))

        plt.bar(
            columnas,
            importancias
        )

        plt.xticks(
            rotation=45
        )

        plt.title(
            "Importancia de Variables"
        )

        plt.tight_layout()

        plt.show()

    # LOGISTICA

    elif algoritmo_actual == "Logistica":

        probabilidades = modelo_entrenado.predict_proba(
            X_test_global
        )[:,1]

        fpr, tpr, _ = roc_curve(
            y_test_global,
            probabilidades
        )

        area = auc(
            fpr,
            tpr
        )

        plt.figure(figsize=(6,6))

        plt.plot(
            fpr,
            tpr,
            label=f"AUC = {area:.3f}"
        )

        plt.plot(
            [0,1],
            [0,1]
        )

        plt.xlabel(
            "False Positive Rate"
        )

        plt.ylabel(
            "True Positive Rate"
        )

        plt.title(
            "Curva ROC"
        )

        plt.legend()

        plt.show()

# ==========================
# VENTANA
# ==========================

ventana = tk.Tk()

ventana.title(
    "Machine Learning Biblioteca"
)

ventana.geometry(
    "1400x800"
)

# ==========================
# FRAME IZQUIERDO
# ==========================

frame_izq = tk.Frame(
    ventana
)

frame_izq.pack(
    side=tk.LEFT,
    fill=tk.Y,
    padx=10,
    pady=10
)

# ==========================
# BOTON ABRIR
# ==========================

btn_abrir = tk.Button(
    frame_izq,
    text="Abrir Excel",
    command=abrir_excel,
    width=25
)

btn_abrir.pack(
    pady=5
)

lbl_archivo = tk.Label(
    frame_izq,
    text="Sin archivo"
)

lbl_archivo.pack(
    pady=5
)

# ==========================
# VARIABLES X
# ==========================

tk.Label(
    frame_izq,
    text="Variables Predictoras (X)"
).pack()

listbox_x = tk.Listbox(
    frame_izq,
    selectmode=tk.MULTIPLE,
    width=30,
    height=12
)

listbox_x.pack(
    pady=5
)

# ==========================
# VARIABLE Y
# ==========================

tk.Label(
    frame_izq,
    text="Variable Objetivo (Y)"
).pack()

combo_y = ttk.Combobox(
    frame_izq,
    width=27
)

combo_y.pack(
    pady=5
)

# ==========================
# ALGORITMOS
# ==========================

algoritmo_var = tk.StringVar()

algoritmo_var.set(
    "Arbol"
)

tk.Label(
    frame_izq,
    text="Algoritmo"
).pack()

tk.Radiobutton(
    frame_izq,
    text="Árbol de Decisión",
    variable=algoritmo_var,
    value="Arbol"
).pack(anchor="w")

tk.Radiobutton(
    frame_izq,
    text="Random Forest",
    variable=algoritmo_var,
    value="Forest"
).pack(anchor="w")

tk.Radiobutton(
    frame_izq,
    text="Regresión Logística",
    variable=algoritmo_var,
    value="Logistica"
).pack(anchor="w")

btn_entrenar = tk.Button(

    frame_izq,

    text="Entrenar Modelo",

    command=entrenar_modelo,

    width=25

)

btn_entrenar.pack(
    pady=5
)

btn_comparar = tk.Button(

    frame_izq,

    text="Comparar Algoritmos",

    command=comparar_algoritmos,

    width=25

)

btn_comparar.pack(
    pady=5
)


# ==========================
# BOTON VALIDAR
# ==========================

btn_validar = tk.Button(
    frame_izq,
    text="Mostrar Configuración",
    command=mostrar_configuracion,
    width=25
)

btn_validar.pack(
    pady=10
)

btn_graficos = tk.Button(
    frame_izq,
    text="Mostrar Gráficos",
    command=mostrar_graficos,
    width=25
)

btn_graficos.pack(
    pady=5
)

# ==========================
# RESULTADOS
# ==========================

txt_resultados = tk.Text(
    frame_izq,
    width=35,
    height=15
)

txt_resultados.pack(
    pady=10
)

# ==========================
# FRAME DERECHO
# ==========================

frame_der = tk.Frame(
    ventana
)

frame_der.pack(
    fill=tk.BOTH,
    expand=True
)

# ==========================
# TREEVIEW
# ==========================

tree = ttk.Treeview(
    frame_der
)

tree.pack(
    fill=tk.BOTH,
    expand=True
)

ventana.mainloop()
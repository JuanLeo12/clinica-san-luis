import tkinter as tk
from tkinter import ttk, filedialog, messagebox

import pandas as pd

# ==========================
# VARIABLES GLOBALES
# ==========================

df = None

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
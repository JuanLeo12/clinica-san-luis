
# Ejecutar: pip install pandas scikit-learn matplotlib openpyxl
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score,precision_score,recall_score,f1_score
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt

ARCHIVO="dataset_random_forest_retrasos_100.xlsx"

class Ventana:
    def __init__(self,root):
        self.root=root
        self.df=pd.read_excel(ARCHIVO)

        ttk.Button(root,text="Entrenar modelo",command=self.entrenar).pack()

        self.tv=ttk.Treeview(root,columns=list(self.df.columns),show="headings",height=10)
        for c in self.df.columns:
            self.tv.heading(c,text=c)
        self.tv.pack(fill="x")
        for _,r in self.df.iterrows():
            self.tv.insert("",tk.END,values=list(r))

        f=ttk.Frame(root); f.pack()

        self.p=tk.Entry(f,width=10); self.p.pack(side="left")
        self.o=tk.Entry(f,width=10); self.o.pack(side="left")
        self.t=tk.Entry(f,width=10); self.t.pack(side="left")

        ttk.Button(f,text="Pronosticar",command=self.predecir).pack(side="left")
        ttk.Button(f,text="Exportar Excel",command=self.exportar).pack(side="left")
        ttk.Button(f,text="Gráficos",command=self.graficos).pack(side="left")

        self.res=ttk.Treeview(root,columns=("Pedidos","Operarios","Tiempo","Resultado"),show="headings")
        for c in ("Pedidos","Operarios","Tiempo","Resultado"):
            self.res.heading(c,text=c)
        self.res.pack(fill="x")

        self.lbl=tk.Label(root,justify="left")
        self.lbl.pack()

    def entrenar(self):
        X=self.df[["Pedidos","Operarios","Tiempo_horas"]]
        y=self.df["Retraso"]

        # Aumenta el test_size a 0.3 o 0.4 para ver si el modelo es capaz de generalizar
        Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.4, random_state=123, stratify=y)

        self.modelo = RandomForestClassifier(
            n_estimators=50,
            max_depth=3,            # Limita qué tan profundo puede analizar los datos
            min_samples_leaf=5,     # Obliga al modelo a agrupar más datos antes de decidir
            random_state=42,
            class_weight='balanced'
            )
        self.modelo.fit(Xtr,ytr)

        atr=accuracy_score(ytr,self.modelo.predict(Xtr))
        p=self.modelo.predict(Xte)

        ate=accuracy_score(yte,p)
        texto=f"""Entrenamiento Accuracy: {atr:.3f}
Prueba Accuracy: {ate:.3f}
Precision: {precision_score(yte,p,pos_label='Sí'):.3f}
Recall: {recall_score(yte,p,pos_label='Sí'):.3f}
F1: {f1_score(yte,p,pos_label='Sí'):.3f}

Comparación: {'Modelo válido' if abs(atr-ate)<0.08 else 'Posible overfitting'}
"""
        self.lbl.config(text=texto)

    def predecir(self):
        # Creamos un pequeño DataFrame con las columnas correctas
        datos_entrada = pd.DataFrame(
            [[float(self.p.get()), float(self.o.get()), float(self.t.get())]],
            columns=["Pedidos", "Operarios", "Tiempo_horas"]
        )
        
        # Usamos ese DataFrame para predecir
        r = self.modelo.predict(datos_entrada)[0]
        
        self.res.insert("", tk.END, values=(self.p.get(), self.o.get(), self.t.get(), r))

    def exportar(self):
        ruta=filedialog.asksaveasfilename(defaultextension=".xlsx")
        if ruta:
            datos=[self.res.item(i)["values"] for i in self.res.get_children()]
            pd.DataFrame(datos,columns=["Pedidos","Operarios","Tiempo","Resultado"]).to_excel(ruta,index=False)

    def graficos(self):
        fig = plt.Figure(figsize=(5, 4))
        ax = fig.add_subplot(111)
        importancias = self.modelo.feature_importances_
        caracteristicas = ["Pedidos", "Operarios", "Tiempo"]
        
        ax.bar(caracteristicas, importancias, color='skyblue')
        ax.set_title("Importancia de las variables en el retraso")
        ax.set_ylim(0, 1) # Asegura que la escala siempre sea de 0 a 1
        
        w = tk.Toplevel()
        c = FigureCanvasTkAgg(fig, w)
        c.draw()
        c.get_tk_widget().pack()

root=tk.Tk()
root.geometry("1000x700")
root.title("Random Forest")
Ventana(root)
root.mainloop()

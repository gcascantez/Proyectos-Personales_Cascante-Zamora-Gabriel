import math
import threading
import customtkinter as ctk
from tkinter import filedialog, messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
import pandas as pd

# Configuración visual
ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")


class DataProcessorApp(ctk.CTk):

    def __init__(self):
        super().__init__()

        self.title("Procesador de Datos - Histograma & Boxplot")
        self.geometry("1150x750")
        self.minsize(950, 650)

        # Almacenamiento de datos
        self.datos = np.array([], dtype=np.float64)
        
        # Canvas para gráficos
        self.canvas_histograma = None
        self.canvas_boxplot = None

        self._crear_interfaz()

    def _crear_interfaz(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=3)
        self.grid_rowconfigure(0, weight=1)

        # =========================================================================
        # PANEL IZQUIERDO: CARGA DE DATOS Y CONTROLES
        # =========================================================================
        self.panel_control = ctk.CTkScrollableFrame(self, corner_radius=10)
        self.panel_control.grid(row=0, column=0, padx=15, pady=15, sticky="nsew")

        # --- CARGA DE DATOS ---
        ctk.CTkLabel(
            self.panel_control,
            text="1. Carga de Datos",
            font=ctk.CTkFont(size=16, weight="bold"),
        ).pack(anchor="w", padx=10, pady=(10, 5))

        self.btn_cargar_csv = ctk.CTkButton(
            self.panel_control,
            text="📁 Seleccionar CSV",
            command=self.cargar_csv,
        )
        self.btn_cargar_csv.pack(fill="x", padx=10, pady=5)

        self.combo_columnas = ctk.CTkComboBox(
            self.panel_control, values=["N/A"], state="disabled"
        )
        self.combo_columnas.pack(fill="x", padx=10, pady=5)

        self.btn_confirmar_columna = ctk.CTkButton(
            self.panel_control,
            text="Cargar Columna",
            fg_color="gray",
            state="disabled",
            command=self.procesar_columna_csv,
        )
        self.btn_confirmar_columna.pack(fill="x", padx=10, pady=5)

        # Entrada Manual
        ctk.CTkLabel(
            self.panel_control,
            text="Ingreso Manual (comas/espacios):",
            font=ctk.CTkFont(size=11),
        ).pack(anchor="w", padx=10, pady=(10, 2))

        self.txt_manual = ctk.CTkTextbox(self.panel_control, height=70)
        self.txt_manual.pack(fill="x", padx=10, pady=2)

        self.btn_cargar_manual = ctk.CTkButton(
            self.panel_control,
            text="➕ Agregar Manuales",
            command=self.cargar_manual,
        )
        self.btn_cargar_manual.pack(fill="x", padx=10, pady=5)

        self.btn_limpiar = ctk.CTkButton(
            self.panel_control,
            text="🗑️ Limpiar Datos",
            fg_color="#D32F2F",
            hover_color="#9A0007",
            command=self.limpiar_datos,
        )
        self.btn_limpiar.pack(fill="x", padx=10, pady=(5, 15))

        # Separador
        ctk.CTkFrame(self.panel_control, height=2, fg_color="gray40").pack(
            fill="x", padx=10, pady=10
        )

        # --- OPCIONES DEL HISTOGRAMA ---
        ctk.CTkLabel(
            self.panel_control,
            text="2. Configuración Histograma",
            font=ctk.CTkFont(size=16, weight="bold"),
        ).pack(anchor="w", padx=10, pady=(5, 5))

        self.var_etiqueta = ctk.StringVar(value="marca")

        self.radio_marca = ctk.CTkRadioButton(
            self.panel_control,
            text="Marca de Clase (Centro)",
            variable=self.var_etiqueta,
            value="marca",
        )
        self.radio_marca.pack(anchor="w", padx=15, pady=5)

        self.radio_rango = ctk.CTkRadioButton(
            self.panel_control,
            text="Rango [Vmin, Vmax]",
            variable=self.var_etiqueta,
            value="rango",
        )
        self.radio_rango.pack(anchor="w", padx=15, pady=5)

        # --- BOTONES DE GENERACIÓN DE GRÁFICOS ---
        ctk.CTkLabel(
            self.panel_control,
            text="3. Visualización",
            font=ctk.CTkFont(size=16, weight="bold"),
        ).pack(anchor="w", padx=10, pady=(15, 5))

        self.btn_generar_histograma = ctk.CTkButton(
            self.panel_control,
            text="📊 Generar Histograma",
            fg_color="#2E7D32",
            hover_color="#1B5E20",
            command=self.generar_histograma,
        )
        self.btn_generar_histograma.pack(fill="x", padx=10, pady=5)

        self.btn_generar_boxplot = ctk.CTkButton(
            self.panel_control,
            text="📦 Generar Boxplot",
            fg_color="#0277BD",
            hover_color="#01579B",
            command=self.generar_boxplot,
        )
        self.btn_generar_boxplot.pack(fill="x", padx=10, pady=(5, 15))

        # =========================================================================
        # PANEL DERECHO: PESTAÑAS DE VISUALIZACIÓN Y RESUMEN
        # =========================================================================
        self.panel_main = ctk.CTkFrame(self, corner_radius=10)
        self.panel_main.grid(row=0, column=1, padx=15, pady=15, sticky="nsew")

        self.lbl_estado = ctk.CTkLabel(
            self.panel_main,
            text="Estado: Esperando datos...",
            font=ctk.CTkFont(size=14, weight="bold"),
        )
        self.lbl_estado.pack(anchor="w", padx=20, pady=(10, 2))

        self.lbl_resumen = ctk.CTkLabel(
            self.panel_main,
            text="Total de registros: 0",
            font=ctk.CTkFont(size=12),
            justify="left",
        )
        self.lbl_resumen.pack(anchor="w", padx=20, pady=(0, 5))

        # Pestañas para separar Histograma y Boxplot
        self.tabview = ctk.CTkTabview(self.panel_main)
        self.tabview.pack(fill="both", expand=True, padx=15, pady=(5, 15))

        self.tab_hist = self.tabview.add("Histograma")
        self.tab_box = self.tabview.add("Diagrama de Cajas y Bigotes")

        # Placeholders iniciales
        self.lbl_ph_hist = ctk.CTkLabel(
            self.tab_hist,
            text="Carga datos y presiona 'Generar Histograma'",
            font=ctk.CTkFont(size=15, slant="italic"),
        )
        self.lbl_ph_hist.place(relx=0.5, rely=0.5, anchor="center")

        self.lbl_ph_box = ctk.CTkLabel(
            self.tab_box,
            text="Carga datos y presiona 'Generar Boxplot'",
            font=ctk.CTkFont(size=15, slant="italic"),
        )
        self.lbl_ph_box.place(relx=0.5, rely=0.5, anchor="center")

    # =========================================================================
    # LÓGICA DEL HISTOGRAMA
    # =========================================================================

    def generar_histograma(self):
        n = len(self.datos)
        if n == 0:
            messagebox.showwarning("Atención", "Primero debes cargar datos numéricos.")
            return

        self.tabview.set("Histograma")

        num_clases = math.ceil(math.sqrt(n))
        v_min, v_max = np.min(self.datos), np.max(self.datos)

        if v_min == v_max:
            v_min -= 0.5
            v_max += 0.5

        epsilon = 1e-6
        v_min_adj = v_min - epsilon
        v_max_adj = v_max + epsilon
        ancho_clase = (v_max_adj - v_min_adj) / num_clases

        bins = [v_min_adj + i * ancho_clase for i in range(num_clases + 1)]
        frecuencias, _ = np.histogram(self.datos, bins=bins)

        etiquetas_x = []
        modo_etiqueta = self.var_etiqueta.get()

        for i in range(num_clases):
            l_inf, l_sup = bins[i], bins[i + 1]
            if modo_etiqueta == "marca":
                centro = (l_sup + l_inf) / 2.0
                etiquetas_x.append(f"{centro:.2f}")
            else:
                etiquetas_x.append(f"[{l_inf:.2f}, {l_sup:.2f}]")

        self._renderizar_histograma(frecuencias, etiquetas_x, num_clases, ancho_clase)

    def _renderizar_histograma(self, frecuencias, etiquetas_x, num_clases, ancho_clase):
        if self.canvas_histograma:
            self.canvas_histograma.get_tk_widget().destroy()

        if hasattr(self, "lbl_ph_hist") and self.lbl_ph_hist.winfo_exists():
            self.lbl_ph_hist.destroy()

        fig, ax = plt.subplots(figsize=(7, 4.5), dpi=100)
        posiciones_x = np.arange(len(frecuencias))

        bars = ax.bar(
            posiciones_x,
            frecuencias,
            width=0.95,
            color="#3B8ED0",
            edgecolor="black",
            align="center",
        )

        ax.set_xticks(posiciones_x)
        ax.set_xticklabels(
            etiquetas_x,
            rotation=45 if self.var_etiqueta.get() == "rango" else 0,
            ha="right" if self.var_etiqueta.get() == "rango" else "center",
        )

        ax.set_title(
            f"Histograma (Clases = {num_clases} | Ancho ≈ {ancho_clase:.4f})",
            fontsize=12,
            fontweight="bold",
        )
        ax.set_xlabel(
            "Marcas de Clase" if self.var_etiqueta.get() == "marca" else "Intervalos [Vmin, Vmax]",
            fontsize=10,
        )
        ax.set_ylabel("Frecuencia Absoluta", fontsize=10)
        ax.grid(axis="y", linestyle="--", alpha=0.7)

        for bar in bars:
            yval = bar.get_height()
            if yval > 0:
                ax.text(
                    bar.get_x() + bar.get_width() / 2.0,
                    yval,
                    f"{int(yval)}",
                    ha="center",
                    va="bottom",
                    fontsize=8,
                )

        fig.tight_layout()
        self.canvas_histograma = FigureCanvasTkAgg(fig, master=self.tab_hist)
        self.canvas_histograma.draw()
        self.canvas_histograma.get_tk_widget().pack(fill="both", expand=True)

    # =========================================================================
    # LÓGICA DEL DIAGRAMA DE CAJAS Y BIGOTES (BOXPLOT)
    # =========================================================================

    def generar_boxplot(self):
        n = len(self.datos)
        if n == 0:
            messagebox.showwarning("Atención", "Primero debes cargar datos numéricos.")
            return

        self.tabview.set("Diagrama de Cajas y Bigotes")

        # 1. Cálculo explícito de Cuartiles y RIQ
        q1 = np.percentile(self.datos, 25)
        q2 = np.percentile(self.datos, 50)  # Mediana
        q3 = np.percentile(self.datos, 75)
        riq = q3 - q1

        # 2. Límites teóricos para bigotes (1.5 * RIQ)
        lim_inf_teorico = q1 - 1.5 * riq
        lim_sup_teorico = q3 + 1.5 * riq

        # 3. Recorte de bigotes a los datos reales dentro del rango
        datos_dentro = self.datos[
            (self.datos >= lim_inf_teorico) & (self.datos <= lim_sup_teorico)
        ]
        
        bigote_inf = np.min(datos_dentro) if len(datos_dentro) > 0 else q1
        bigote_sup = np.max(datos_dentro) if len(datos_dentro) > 0 else q3

        # Outliers (puntos fuera de los bigotes)
        outliers = self.datos[
            (self.datos < lim_inf_teorico) | (self.datos > lim_sup_teorico)
        ]

        self._renderizar_boxplot(q1, q2, q3, riq, bigote_inf, bigote_sup, outliers)

    def _renderizar_boxplot(
        self, q1, q2, q3, riq, bigote_inf, bigote_sup, outliers
    ):
        if self.canvas_boxplot:
            self.canvas_boxplot.get_tk_widget().destroy()

        if hasattr(self, "lbl_ph_box") and self.lbl_ph_box.winfo_exists():
            self.lbl_ph_box.destroy()

        fig, ax = plt.subplots(figsize=(7, 4.5), dpi=100)

        # Propiedades del boxplot
        flierprops = dict(
            marker="o",
            markerfacecolor="none",
            markeredgecolor="#D32F2F",
            markersize=6,
            linestyle="none",
        )
        boxprops = dict(facecolor="#90CAF9", color="#0D47A1", linewidth=1.5)
        whiskerprops = dict(color="#0D47A1", linewidth=1.5)
        capprops = dict(color="#0D47A1", linewidth=1.5)
        medianprops = dict(color="#B71C1C", linewidth=2.0)

        # Creación del Boxplot con matplotlib (usando tick_labels)
        ax.boxplot(
            self.datos,
            orientation="vertical",
            patch_artist=True,
            whis=1.5,
            flierprops=flierprops,
            boxprops=boxprops,
            whiskerprops=whiskerprops,
            capprops=capprops,
            medianprops=medianprops,
            tick_labels=["Conjunto de Datos"],  # Parámetro actualizado
        )

        ax.set_title(
            f"Boxplot (Q1={q1:.2f} | Mediana={q2:.2f} | Q3={q3:.2f} | RIQ={riq:.2f})",
            fontsize=11,
            fontweight="bold",
        )
        ax.set_ylabel("Valores", fontsize=10)
        ax.grid(axis="y", linestyle="--", alpha=0.7)

        fig.tight_layout()

        self.canvas_boxplot = FigureCanvasTkAgg(fig, master=self.tab_box)
        self.canvas_boxplot.draw()
        self.canvas_boxplot.get_tk_widget().pack(fill="both", expand=True)

    # =========================================================================
    # MÉTODOS DE CARGA Y LIMPIEZA DE DATOS
    # =========================================================================

    def cargar_csv(self):
        ruta = filedialog.askopenfilename(
            filetypes=[("Archivos CSV", "*.csv"), ("Todos", "*.*")]
        )
        if not ruta:
            return
        self.lbl_estado.configure(text="Estado: Analizando CSV...")
        threading.Thread(
            target=self._leer_csv_thread, args=(ruta,), daemon=True
        ).start()

    def _leer_csv_thread(self, ruta):
        try:
            self.ruta_csv_actual = ruta
            cols = pd.read_csv(ruta, nrows=1000).columns
            cols_num = []
            for c in cols:
                try:
                    pd.to_numeric(pd.read_csv(ruta, usecols=[c], nrows=100)[c])
                    cols_num.append(c)
                except Exception:
                    continue
            self.after(0, self._actualizar_combo, cols_num)
        except Exception as e:
            messagebox.showerror("Error", f"Error al leer CSV:\n{str(e)}")

    def _actualizar_combo(self, columnas):
        if columnas:
            self.combo_columnas.configure(state="normal", values=columnas)
            self.combo_columnas.set(columnas[0])
            self.btn_confirmar_columna.configure(
                state="normal", fg_color=["#3B8ED0", "#1F6AA5"]
            )
            self.lbl_estado.configure(text="Estado: Selecciona columna.")

    def procesar_columna_csv(self):
        col = self.combo_columnas.get()
        if not col or col == "N/A":
            return

        def _cargar():
            s = pd.read_csv(self.ruta_csv_actual, usecols=[col])[col]
            s = pd.to_numeric(s, errors="coerce").dropna()
            self.datos = np.concatenate([self.datos, s.to_numpy(dtype=np.float64)])
            self.after(0, self._actualizar_resumen)

        threading.Thread(target=_cargar, daemon=True).start()

    def cargar_manual(self):
        texto = self.txt_manual.get("1.0", "end").strip()
        if not texto:
            return
        try:
            limpio = texto.replace(",", " ").replace("\n", " ")
            vals = [float(x) for x in limpio.split() if x.strip() != ""]
            if vals:
                self.datos = np.concatenate(
                    [self.datos, np.array(vals, dtype=np.float64)]
                )
                self.txt_manual.delete("1.0", "end")
                self._actualizar_resumen()
        except ValueError:
            messagebox.showerror("Error", "Ingresa únicamente números válidos.")

    def _actualizar_resumen(self):
        n = len(self.datos)
        if n > 0:
            q1 = np.percentile(self.datos, 25)
            q2 = np.percentile(self.datos, 50)
            q3 = np.percentile(self.datos, 75)
            riq = q3 - q1
            self.lbl_resumen.configure(
                text=f"Registros: {n:,} | Mín: {np.min(self.datos):.2f} | Q1: {q1:.2f} | Mediana: {q2:.2f} | Q3: {q3:.2f} | RIQ: {riq:.2f} | Máx: {np.max(self.datos):.2f}"
            )
            self.lbl_estado.configure(text=f"Estado: {n:,} datos cargados.")
        else:
            self.lbl_resumen.configure(text="Total de registros: 0")
            self.lbl_estado.configure(text="Estado: Sin datos.")

    def limpiar_datos(self):
        self.datos = np.array([], dtype=np.float64)
        if self.canvas_histograma:
            self.canvas_histograma.get_tk_widget().destroy()
            self.canvas_histograma = None
        if self.canvas_boxplot:
            self.canvas_boxplot.get_tk_widget().destroy()
            self.canvas_boxplot = None
        self._actualizar_resumen()


if __name__ == "__main__":
    app = DataProcessorApp()
    app.mainloop()


if __name__ == "__main__":
    app = DataProcessorApp()
    app.mainloop()

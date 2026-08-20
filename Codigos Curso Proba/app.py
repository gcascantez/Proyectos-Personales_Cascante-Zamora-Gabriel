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

        self.title("Procesador de Datos - Histograma Personalizado")
        self.geometry("1100x700")
        self.minsize(950, 600)

        # Almacenamiento de datos
        self.datos = np.array([], dtype=np.float64)
        self.canvas_histograma = None

        self._crear_interfaz()

    def _crear_interfaz(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=3)
        self.grid_rowconfigure(0, weight=1)

        # =========================================================================
        # PANEL IZQUIERDO: CARGA DE DATOS Y CONTROLES DEL HISTOGRAMA
        # =========================================================================
        self.panel_control = ctk.CTkScrollableFrame(self, corner_radius=10)
        self.panel_control.grid(
            row=0, column=0, padx=15, pady=15, sticky="nsew"
        )

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
            text="2. Opción de Etiquetas (Eje X)",
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

        self.btn_generar_histograma = ctk.CTkButton(
            self.panel_control,
            text="📊 Generar Histograma",
            fg_color="#2E7D32",
            hover_color="#1B5E20",
            command=self.generar_histograma,
        )
        self.btn_generar_histograma.pack(fill="x", padx=10, pady=(15, 10))

        # =========================================================================
        # PANEL DERECHO: ÁREA DE GRÁFICOS Y ESTADÍSTICAS
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

        # Marco para incrustar el gráfico de Matplotlib
        self.frame_grafico = ctk.CTkFrame(self.panel_main)
        self.frame_grafico.pack(
            fill="both", expand=True, padx=15, pady=(5, 15)
        )

        self.lbl_placeholder = ctk.CTkLabel(
            self.frame_grafico,
            text="Carga datos y presiona 'Generar Histograma'",
            font=ctk.CTkFont(size=15, slant="italic"),
        )
        self.lbl_placeholder.place(relx=0.5, rely=0.5, anchor="center")

    # =========================================================================
    # LÓGICA DE HISTOGRAMA CON LAS TRES REGLAS
    # =========================================================================

    def generar_histograma(self):
        n = len(self.datos)
        if n == 0:
            messagebox.showwarning(
                "Atención", "Primero debes cargar datos numéricos."
            )
            return

        # --- Regla 1: Cantidad de clases = ceil(sqrt(n)) ---
        num_clases = math.ceil(math.sqrt(n))

        v_min = np.min(self.datos)
        v_max = np.max(self.datos)

        # Prevenir error si todos los datos son idénticos
        if v_min == v_max:
            v_min -= 0.5
            v_max += 0.5

        # --- Regla 2: Desfase para que NINGÚN límite toque valores de los datos ---
        epsilon = 1e-6
        v_min_adj = v_min - epsilon
        v_max_adj = v_max + epsilon

        # Ancho de clase basado en el rango ajustado
        ancho_clase = (v_max_adj - v_min_adj) / num_clases

        # Construcción de los bordes de los intervalos
        bins = [v_min_adj + i * ancho_clase for i in range(num_clases + 1)]

        # Conteo de frecuencias en cada clase
        frecuencias, _ = np.histogram(self.datos, bins=bins)

        # --- Regla 3: Determinación de Identificadores (Eje X) ---
        etiquetas_x = []
        modo_etiqueta = self.var_etiqueta.get()

        for i in range(num_clases):
            l_inf = bins[i]
            l_sup = bins[i + 1]

            if modo_etiqueta == "marca":
                # Marca de clase (Centro del intervalo)
                centro = (l_sup + l_inf) / 2.0
                etiquetas_x.append(f"{centro:.2f}")
            else:
                # Formato Rango [Vmin, Vmax]
                etiquetas_x.append(f"[{l_inf:.2f}, {l_sup:.2f}]")

        # --- DIBUJAR EN MATPLOTLIB ---
        self._renderizar_grafico(
            frecuencias, etiquetas_x, num_clases, ancho_clase
        )

    def _renderizar_grafico(
        self, frecuencias, etiquetas_x, num_clases, ancho_clase
    ):
        # Limpiar gráfico previo si existe
        if self.canvas_histograma:
            self.canvas_histograma.get_tk_widget().destroy()

        if hasattr(self, "lbl_placeholder"):
            self.lbl_placeholder.destroy()

        # Crear figura de Matplotlib
        fig, ax = plt.subplots(figsize=(7, 4.5), dpi=100)

        posiciones_x = np.arange(len(frecuencias))

        # Gráfico de barras representando las clases
        bars = ax.bar(
            posiciones_x,
            frecuencias,
            width=0.95,
            color="#3B8ED0",
            edgecolor="black",
            align="center",
        )

        # Configuración de ejes y etiquetas
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
            "Marcas de Clase"
            if self.var_etiqueta.get() == "marca"
            else "Intervalos [Vmin, Vmax]",
            fontsize=10,
        )
        ax.set_ylabel("Frecuencia Absoluta", fontsize=10)
        ax.grid(axis="y", linestyle="--", alpha=0.7)

        # Mostrar valores numéricos sobre cada barra
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

        # Incrustar gráfico en la ventana de Tkinter
        self.canvas_histograma = FigureCanvasTkAgg(fig, master=self.frame_grafico)
        self.canvas_histograma.draw()
        self.canvas_histograma.get_tk_widget().pack(fill="both", expand=True)

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
                    pd.to_numeric(
                        pd.read_csv(ruta, usecols=[c], nrows=100)[c]
                    )
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
            messagebox.showerror(
                "Error", "Ingresa únicamente números válidos."
            )

    def _actualizar_resumen(self):
        n = len(self.datos)
        if n > 0:
            self.lbl_resumen.configure(
                text=f"Registros: {n:,} | Mín: {np.min(self.datos):.4f} | Máx: {np.max(self.datos):.4f}"
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
        self._actualizar_resumen()


if __name__ == "__main__":
    app = DataProcessorApp()
    app.mainloop()
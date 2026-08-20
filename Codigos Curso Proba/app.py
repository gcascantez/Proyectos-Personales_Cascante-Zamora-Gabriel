import math
import threading
import customtkinter as ctk
from tkinter import filedialog, messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
import pandas as pd

# =========================================================================
# CONFIGURACIÓN DEL TEMA VISUAL DE LA INTERFAZ
# =========================================================================
ctk.set_appearance_mode("System")  # Adaptación automática a modo claro/oscuro
ctk.set_default_color_theme("blue")  # Esquema de color azul por defecto


class DataProcessorApp(ctk.CTk):
    """
    Aplicación principal para la carga, gestión y visualización de datos numéricos
    utilizando Histogramas y Diagramas de Cajas y Bigotes Múltiples.
    """

    def __init__(self):
        super().__init__()

        # --- Configuración básica de la ventana principal ---
        self.title("Procesador de Datos - Histograma & Boxplots Múltiples")
        self.geometry("1150x750")
        self.minsize(950, 650)

        # --- Estructura de almacenamiento central ---
        # Diccionario para almacenar muestras activas: { "Nombre_Muestra": np.array([...]) }
        self.grupos = {}

        # Referencias a los canvas de Matplotlib embedded en Tkinter
        self.canvas_histograma = None
        self.canvas_boxplot = None

        # --- Construcción de la GUI ---
        self._crear_interfaz()

        # Vinculación del evento de cierre para liberar recursos de Matplotlib/Threads
        self.protocol("WM_DELETE_WINDOW", self.destroy)

    def destroy(self):
        """Manejo de cierre limpio para evitar congelamientos en la terminal."""
        plt.close("all")  # Cierra todas las figuras de Matplotlib en memoria
        super().destroy()

    def _crear_interfaz(self):
        """Diseña la distribución de paneles y controles de la aplicación."""
        # Grid principal: Columna 0 (Controles), Columna 1 (Gráficos)
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=3)
        self.grid_rowconfigure(0, weight=1)

        # =========================================================================
        # PANEL IZQUIERDO: CONTROLES DE ENTRADA Y GESTIÓN (Scrollable)
        # =========================================================================
        self.panel_control = ctk.CTkScrollableFrame(self, corner_radius=10)
        self.panel_control.grid(
            row=0, column=0, padx=15, pady=15, sticky="nsew"
        )

        # --- SECCIÓN 1: CARGA DE DATOS ---
        ctk.CTkLabel(
            self.panel_control,
            text="1. Carga de Datos",
            font=ctk.CTkFont(size=16, weight="bold"),
        ).pack(anchor="w", padx=10, pady=(10, 5))

        # Entradas para la muestra
        ctk.CTkLabel(
            self.panel_control,
            text="Nombre de la Muestra / Serie:",
            font=ctk.CTkFont(size=11, weight="bold"),
        ).pack(anchor="w", padx=10, pady=(5, 2))

        self.ent_nombre_grupo = ctk.CTkEntry(
            self.panel_control, placeholder_text="Ej: Muestra A"
        )
        self.ent_nombre_grupo.pack(fill="x", padx=10, pady=(0, 10))

        # Controles para CSV
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

        # Controles para ingreso manual
        ctk.CTkLabel(
            self.panel_control,
            text="Ingreso Manual (comas/espacios):",
            font=ctk.CTkFont(size=11),
        ).pack(anchor="w", padx=10, pady=(10, 2))

        self.txt_manual = ctk.CTkTextbox(self.panel_control, height=65)
        self.txt_manual.pack(fill="x", padx=10, pady=2)

        self.btn_cargar_manual = ctk.CTkButton(
            self.panel_control,
            text="➕ Agregar Conjunto Manual",
            command=self.cargar_manual,
        )
        self.btn_cargar_manual.pack(fill="x", padx=10, pady=5)

        # Separador visual
        ctk.CTkFrame(self.panel_control, height=2, fg_color="gray40").pack(
            fill="x", padx=10, pady=10
        )

        # --- SECCIÓN 2: GESTIÓN DE MUESTRAS (RENOMBRAR / ELIMINAR) ---
        ctk.CTkLabel(
            self.panel_control,
            text="2. Gestión de Muestras",
            font=ctk.CTkFont(size=16, weight="bold"),
        ).pack(anchor="w", padx=10, pady=(5, 5))

        # Controles de Renombrado
        ctk.CTkLabel(
            self.panel_control,
            text="Renombrar Muestra:",
            font=ctk.CTkFont(size=11, weight="bold"),
        ).pack(anchor="w", padx=10, pady=(2, 2))

        self.combo_renombrar = ctk.CTkComboBox(
            self.panel_control, values=["N/A"], state="disabled"
        )
        self.combo_renombrar.pack(fill="x", padx=10, pady=2)

        self.ent_nuevo_nombre = ctk.CTkEntry(
            self.panel_control, placeholder_text="Nuevo nombre..."
        )
        self.ent_nuevo_nombre.pack(fill="x", padx=10, pady=2)

        self.btn_renombrar = ctk.CTkButton(
            self.panel_control,
            text="✏️ Cambiar Nombre",
            fg_color="#E65100",
            hover_color="#B23C00",
            command=self.renombrar_muestra,
        )
        self.btn_renombrar.pack(fill="x", padx=10, pady=(2, 10))

        # Controles de Eliminación Individual
        ctk.CTkLabel(
            self.panel_control,
            text="Eliminar Muestra Individual:",
            font=ctk.CTkFont(size=11, weight="bold"),
        ).pack(anchor="w", padx=10, pady=(5, 2))

        self.combo_eliminar = ctk.CTkComboBox(
            self.panel_control, values=["N/A"], state="disabled"
        )
        self.combo_eliminar.pack(fill="x", padx=10, pady=2)

        self.btn_eliminar_individual = ctk.CTkButton(
            self.panel_control,
            text="🗑️ Eliminar Seleccionada",
            fg_color="#C62828",
            hover_color="#8E0000",
            command=self.eliminar_muestra_individual,
        )
        self.btn_eliminar_individual.pack(fill="x", padx=10, pady=(2, 5))

        # Separador visual
        ctk.CTkFrame(self.panel_control, height=2, fg_color="gray40").pack(
            fill="x", padx=10, pady=10
        )

        # --- SECCIÓN 3: CONFIGURACIÓN DEL HISTOGRAMA ---
        ctk.CTkLabel(
            self.panel_control,
            text="3. Configuración Histograma",
            font=ctk.CTkFont(size=16, weight="bold"),
        ).pack(anchor="w", padx=10, pady=(5, 5))

        ctk.CTkLabel(
            self.panel_control,
            text="Muestra a Graficar:",
            font=ctk.CTkFont(size=11),
        ).pack(anchor="w", padx=10, pady=(2, 2))

        self.combo_grupo_hist = ctk.CTkComboBox(
            self.panel_control, values=["N/A"], state="disabled"
        )
        self.combo_grupo_hist.pack(fill="x", padx=10, pady=5)

        # Opciones para el identificador de clase del Eje X
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

        # --- SECCIÓN 4: ACCIONES Y VISUALIZACIÓN ---
        ctk.CTkLabel(
            self.panel_control,
            text="4. Visualización",
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
            text="📦 Generar Boxplots Múltiples",
            fg_color="#0277BD",
            hover_color="#01579B",
            command=self.generar_boxplot,
        )
        self.btn_generar_boxplot.pack(fill="x", padx=10, pady=5)

        self.btn_limpiar = ctk.CTkButton(
            self.panel_control,
            text="🔥 Limpiar TODOS los Datos",
            fg_color="#333333",
            hover_color="#111111",
            command=self.limpiar_datos,
        )
        self.btn_limpiar.pack(fill="x", padx=10, pady=(10, 15))

        # =========================================================================
        # PANEL DERECHO: ÁREA PRINCIPAL DE GRÁFICOS Y ESTADÍSTICAS
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
            text="Conjuntos cargados: 0",
            font=ctk.CTkFont(size=12),
            justify="left",
        )
        self.lbl_resumen.pack(anchor="w", padx=20, pady=(0, 5))

        # Pestañas para organizar la visualización
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
            text="Carga datos y presiona 'Generar Boxplots Múltiples'",
            font=ctk.CTkFont(size=15, slant="italic"),
        )
        self.lbl_ph_box.place(relx=0.5, rely=0.5, anchor="center")

    # =========================================================================
    # LÓGICA DE GESTIÓN DE MUESTRAS (RENOMBRAR / ELIMINAR)
    # =========================================================================

    def renombrar_muestra(self):
        """Cambia la clave del diccionario de datos sin redibujar el gráfico."""
        nombre_actual = self.combo_renombrar.get()
        nuevo_nombre = self.ent_nuevo_nombre.get().strip()

        if not self.grupos or nombre_actual not in self.grupos:
            messagebox.showwarning(
                "Atención", "Selecciona una muestra válida para renombrar."
            )
            return

        if not nuevo_nombre:
            messagebox.showwarning(
                "Atención", "Ingresa un nuevo nombre válido."
            )
            return

        if nuevo_nombre in self.grupos and nuevo_nombre != nombre_actual:
            messagebox.showerror(
                "Error", "Ya existe una muestra con ese nombre."
            )
            return

        # Reestructuración del diccionario preservando el orden secuencial
        nuevos_grupos = {}
        for k, v in self.grupos.items():
            if k == nombre_actual:
                nuevos_grupos[nuevo_nombre] = v
            else:
                nuevos_grupos[k] = v

        self.grupos = nuevos_grupos
        self.ent_nuevo_nombre.delete(0, "end")
        self._actualizar_combos()
        self._actualizar_resumen()

        self.lbl_estado.configure(
            text=f"Estado: Muestra renombrada a '{nuevo_nombre}'. Presiona 'Generar Boxplot' para actualizar."
        )

    def eliminar_muestra_individual(self):
        """Elimina únicamente la muestra seleccionada del diccionario."""
        nombre_eliminar = self.combo_eliminar.get()

        if not self.grupos or nombre_eliminar not in self.grupos:
            messagebox.showwarning(
                "Atención", "Selecciona una muestra válida para eliminar."
            )
            return

        del self.grupos[nombre_eliminar]

        self._actualizar_combos()
        self._actualizar_resumen()

        self.lbl_estado.configure(
            text=f"Estado: Muestra '{nombre_eliminar}' eliminada. Presiona 'Generar Boxplot' para actualizar."
        )

    # =========================================================================
    # LÓGICA DEL HISTOGRAMA (REGLAS MATEMÁTICAS)
    # =========================================================================

    def generar_histograma(self):
        """Prepara los datos y calcula las clases bajo las reglas definidas."""
        nombre_grupo = self.combo_grupo_hist.get()
        if not nombre_grupo or nombre_grupo not in self.grupos:
            messagebox.showwarning(
                "Atención", "Selecciona una muestra válida para el histograma."
            )
            return

        self.tabview.set("Histograma")
        datos = self.grupos[nombre_grupo]
        n = len(datos)

        # REGLA 1: Cantidad de clases k = ceil(sqrt(n))
        num_clases = math.ceil(math.sqrt(n))
        v_min, v_max = np.min(datos), np.max(datos)

        if v_min == v_max:
            v_min -= 0.5
            v_max += 0.5

        # REGLA 2: Desfase infinitesimal epsilon para no tocar valores exactos de los datos
        epsilon = 1e-6
        v_min_adj = v_min - epsilon
        v_max_adj = v_max + epsilon

        # Ancho de clase W
        ancho_clase = (v_max_adj - v_min_adj) / num_clases

        # Arreglo de bordes de intervalos (bins)
        bins = [v_min_adj + i * ancho_clase for i in range(num_clases + 1)]
        frecuencias, _ = np.histogram(datos, bins=bins)

        # REGLA 3: Formateo de Etiquetas (Eje X)
        etiquetas_x = []
        modo_etiqueta = self.var_etiqueta.get()

        for i in range(num_clases):
            l_inf, l_sup = bins[i], bins[i + 1]
            if modo_etiqueta == "marca":
                # Opción 1: Marca de clase (Centro del intervalo)
                centro = (l_sup + l_inf) / 2.0
                etiquetas_x.append(f"{centro:.2f}")
            else:
                # Opción 2: Rango explícito de la clase [Vmin, Vmax]
                etiquetas_x.append(f"[{l_inf:.2f}, {l_sup:.2f}]")

        self._renderizar_histograma(
            frecuencias, etiquetas_x, num_clases, ancho_clase, nombre_grupo
        )

    def _renderizar_histograma(
        self, frecuencias, etiquetas_x, num_clases, ancho_clase, titulo_muestra
    ):
        """Incrusta la gráfica del histograma en la interfaz mediante Matplotlib."""
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
            f"Histograma: {titulo_muestra} (Clases = {num_clases} | Ancho ≈ {ancho_clase:.4f})",
            fontsize=11,
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

        # Frecuencias sobre cada barra
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
    # LÓGICA DEL BOXPLOT MULTIVARIABLE (CRITERIO DE TUKEY)
    # =========================================================================

    def generar_boxplot(self):
        """Valida las muestras activas y lanza el renderizado del Diagrama de Cajas."""
        if not self.grupos:
            messagebox.showwarning(
                "Atención", "Primero debes cargar al menos un conjunto de datos."
            )
            return

        self.tabview.set("Diagrama de Cajas y Bigotes")
        self._renderizar_boxplot_multiple(self.grupos)

    def _renderizar_boxplot_multiple(self, diccionario_grupos):
        """Renderiza múltiples diagramas de caja en paralelo usando Matplotlib."""
        if self.canvas_boxplot:
            self.canvas_boxplot.get_tk_widget().destroy()

        if hasattr(self, "lbl_ph_box") and self.lbl_ph_box.winfo_exists():
            self.lbl_ph_box.destroy()

        fig, ax = plt.subplots(figsize=(7, 4.5), dpi=100)

        nombres = list(diccionario_grupos.keys())
        datos_grupos = list(diccionario_grupos.values())

        # Configuración estética de outliers (círculos vacíos)
        flierprops = dict(
            marker="o",
            markerfacecolor="none",
            markeredgecolor="#D32F2F",
            markersize=6,
            linestyle="none",
        )
        medianprops = dict(color="#B71C1C", linewidth=2.0)
        whiskerprops = dict(color="#333333", linewidth=1.5)
        capprops = dict(color="#333333", linewidth=1.5)

        # Construcción del boxplot múltiple
        bp = ax.boxplot(
            datos_grupos,
            orientation="vertical",
            patch_artist=True,
            whis=1.5,  # Bigotes extendidos a 1.5 * RIQ
            flierprops=flierprops,
            medianprops=medianprops,
            whiskerprops=whiskerprops,
            capprops=capprops,
            tick_labels=nombres,  # Asignación de nombres en el eje X
        )

        # Asignación cromática por caja
        colores = [
            "#90CAF9",
            "#A5D6A7",
            "#FFE082",
            "#FFAB91",
            "#CE93D8",
            "#80CBC4",
        ]
        for i, box in enumerate(bp["boxes"]):
            box.set_facecolor(colores[i % len(colores)])
            box.set_edgecolor("#333333")
            box.set_linewidth(1.2)

        ax.set_title(
            f"Comparativa de Diagramas de Cajas y Bigotes ({len(nombres)} muestras)",
            fontsize=12,
            fontweight="bold",
        )
        ax.set_ylabel("Valores", fontsize=10)
        ax.grid(axis="y", linestyle="--", alpha=0.7)

        fig.tight_layout()

        self.canvas_boxplot = FigureCanvasTkAgg(fig, master=self.tab_box)
        self.canvas_boxplot.draw()
        self.canvas_boxplot.get_tk_widget().pack(fill="both", expand=True)

    # =========================================================================
    # MÉTODOS DE CARGA DE ARCHIVOS Y AUXILIARES
    # =========================================================================

    def _obtener_nombre_grupo_valido(self):
        """Genera un nombre por defecto si el usuario no especifica uno."""
        nombre = self.ent_nombre_grupo.get().strip()
        if not nombre:
            nombre = f"Muestra {len(self.grupos) + 1}"
        return nombre

    def cargar_csv(self):
        """Abre un diálogo de archivo y ejecuta la lectura en un hilo secundario."""
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
        """Identifica columnas numéricas sin bloquear la interfaz."""
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
            self.after(0, self._actualizar_combo_csv, cols_num)
        except Exception as e:
            messagebox.showerror("Error", f"Error al leer CSV:\n{str(e)}")

    def _actualizar_combo_csv(self, columnas):
        """Habilita la selección de columna en la GUI."""
        if columnas:
            self.combo_columnas.configure(state="normal", values=columnas)
            self.combo_columnas.set(columnas[0])
            self.btn_confirmar_columna.configure(
                state="normal", fg_color=["#3B8ED0", "#1F6AA5"]
            )
            self.lbl_estado.configure(text="Estado: Selecciona columna.")

    def procesar_columna_csv(self):
        """Extrae la columna seleccionada y la guarda como vector de NumPy."""
        col = self.combo_columnas.get()
        if not col or col == "N/A":
            return

        nombre_grupo = self._obtener_nombre_grupo_valido()

        def _cargar():
            s = pd.read_csv(self.ruta_csv_actual, usecols=[col])[col]
            s = pd.to_numeric(s, errors="coerce").dropna()
            nuevos_datos = s.to_numpy(dtype=np.float64)

            self.grupos[nombre_grupo] = nuevos_datos
            self.after(0, self._actualizar_interfaz_tras_carga)

        threading.Thread(target=_cargar, daemon=True).start()

    def cargar_manual(self):
        """Parsea la entrada de texto manual y la añade al diccionario."""
        texto = self.txt_manual.get("1.0", "end").strip()
        if not texto:
            return
        try:
            limpio = texto.replace(",", " ").replace("\n", " ")
            vals = [float(x) for x in limpio.split() if x.strip() != ""]
            if vals:
                nombre_grupo = self._obtener_nombre_grupo_valido()
                self.grupos[nombre_grupo] = np.array(vals, dtype=np.float64)
                self.txt_manual.delete("1.0", "end")
                self._actualizar_interfaz_tras_carga()
        except ValueError:
            messagebox.showerror("Error", "Ingresa únicamente números válidos.")

    def _actualizar_combos(self):
        """Sincroniza el contenido de todos los menus desplegables."""
        nombres = list(self.grupos.keys())
        if nombres:
            self.combo_grupo_hist.configure(state="normal", values=nombres)
            self.combo_renombrar.configure(state="normal", values=nombres)
            self.combo_eliminar.configure(state="normal", values=nombres)

            if self.combo_grupo_hist.get() not in nombres:
                self.combo_grupo_hist.set(nombres[-1])
            if self.combo_renombrar.get() not in nombres:
                self.combo_renombrar.set(nombres[-1])
            if self.combo_eliminar.get() not in nombres:
                self.combo_eliminar.set(nombres[-1])
        else:
            self.combo_grupo_hist.configure(state="disabled", values=["N/A"])
            self.combo_grupo_hist.set("N/A")
            self.combo_renombrar.configure(state="disabled", values=["N/A"])
            self.combo_renombrar.set("N/A")
            self.combo_eliminar.configure(state="disabled", values=["N/A"])
            self.combo_eliminar.set("N/A")

    def _actualizar_resumen(self):
        """Actualiza las etiquetas informativas del panel superior."""
        total_datos = sum(len(v) for v in self.grupos.values())
        self.lbl_resumen.configure(
            text=f"Muestras cargadas: {len(self.grupos)} | Datos totales: {total_datos:,}"
        )

    def _actualizar_interfaz_tras_carga(self):
        """Actualiza estados de la interfaz tras incorporar una nueva muestra."""
        self._actualizar_combos()
        self._actualizar_resumen()
        self.ent_nombre_grupo.delete(0, "end")

        nombres = list(self.grupos.keys())
        self.lbl_estado.configure(
            text=f"Estado: Muestra '{nombres[-1]}' cargada con éxito."
        )

    def limpiar_datos(self):
        """Limpia todo el almacenamiento de muestras y destruye los canvas activos."""
        self.grupos.clear()
        self._actualizar_combos()
        self._actualizar_resumen()
        self.combo_columnas.configure(state="disabled", values=["N/A"])
        self.combo_columnas.set("N/A")
        self.btn_confirmar_columna.configure(state="disabled", fg_color="gray")

        if self.canvas_histograma:
            self.canvas_histograma.get_tk_widget().destroy()
            self.canvas_histograma = None
        if self.canvas_boxplot:
            self.canvas_boxplot.get_tk_widget().destroy()
            self.canvas_boxplot = None

        self.lbl_estado.configure(text="Estado: Todos los datos han sido limpiados.")


# =========================================================================
# PUNTO DE ENTRADA DE LA APLICACIÓN
# =========================================================================
if __name__ == "__main__":
    app = DataProcessorApp()
    app.mainloop()

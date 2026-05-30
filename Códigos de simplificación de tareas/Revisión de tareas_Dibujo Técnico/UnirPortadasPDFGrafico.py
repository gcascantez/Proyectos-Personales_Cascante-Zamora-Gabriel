import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from pypdf import PdfWriter


def unir_portada_con_nombre_original(pdf_principal, carpeta_fuente, etiqueta_estado):
    try:
        # 1. OBTENER LA RUTA AUTOMÁTICA A "DOWNLOADS"
        carpeta_usuario = os.path.expanduser("~")
        carpeta_salida = os.path.join(
            carpeta_usuario, "Downloads", "resultados_combinados"
        )

        os.makedirs(carpeta_salida, exist_ok=True)

        archivos = [
            f
            for f in os.listdir(carpeta_fuente)
            if f.endswith(".pdf") and f != os.path.basename(pdf_principal)
        ]

        if not archivos:
            messagebox.showwarning(
                "Atención",
                "No se encontraron otros archivos PDF en la carpeta seleccionada.",
            )
            return

        for archivo in archivos:
            ruta_pdf_secundario = os.path.join(carpeta_fuente, archivo)

            fusionador = PdfWriter()
            fusionador.append(pdf_principal)
            fusionador.append(ruta_pdf_secundario)

            ruta_salida = os.path.join(carpeta_salida, archivo)
            with open(ruta_salida, "wb") as archivo_final:
                fusionador.write(archivo_final)

            fusionador.close()

        # Mensaje de éxito al finalizar
        etiqueta_estado.config(
            text=f"¡Proceso completado con éxito!", fg="green"
        )
        messagebox.showinfo(
            "Éxito", f"Archivos guardados en:\n{carpeta_salida}"
        )

    except Exception as e:
        etiqueta_estado.config(text="Error en el proceso.", fg="red")
        messagebox.showerror("Error", f"Ocurrió un error: {str(e)}")


# --- FUNCIONES DE LA INTERFAZ GRÁFICA ---


def seleccionar_pdf():
    ruta = filedialog.askopenfilename(
        title="Seleccionar PDF Principal (Portada)",
        filetypes=[("Archivos PDF", "*.pdf")],
    )
    if ruta:
        entrada_pdf.delete(0, tk.END)
        entrada_pdf.insert(0, ruta)


def seleccionar_carpeta():
    ruta = filedialog.askdirectory(title="Seleccionar Carpeta Fuente")
    if ruta:
        entrada_carpeta.delete(0, tk.END)
        entrada_carpeta.insert(0, ruta)


def iniciar_fusion():
    pdf = entrada_pdf.get()
    carpeta = entrada_carpeta.get()

    if not pdf or not carpeta:
        messagebox.showwarning(
            "Campos vacíos", "Por favor, selecciona ambos campos antes de continuar."
        )
        return

    lbl_estado.config(text="Procesando archivos...", fg="blue")
    # Forzar actualización de la interfaz
    ventana.update_idletasks()

    unir_portada_con_nombre_original(pdf, carpeta, lbl_estado)


# --- CONFIGURACIÓN DE LA VENTANA PRINCIPAL ---
ventana = tk.Tk()
ventana.title("Fusionador de PDF - Portada Automática")
ventana.geometry("600x280")
ventana.resizable(False, False)

# Contenedor principal con márgenes
frame = ttk.Frame(ventana, padding="20")
frame.pack(fill=tk.BOTH, expand=True)

# Sección PDF Principal
ttk.Label(frame, text="PDF Principal (Portada):", font=("Arial", 10, "bold")).grid(
    row=0, column=0, sticky="w", pady=(0, 5)
)
entrada_pdf = ttk.Entry(frame, width=50)
entrada_pdf.grid(row=1, column=0, padx=(0, 10), pady=(0, 15), sticky="we")
btn_buscar_pdf = ttk.Button(frame, text="Buscar Archivo", command=seleccionar_pdf)
btn_buscar_pdf.grid(row=1, column=1, pady=(0, 15))

# Sección Carpeta Fuente
ttk.Label(
    frame, text="Carpeta con PDFs a los que unir la portada:", font=("Arial", 10, "bold")
).grid(row=2, column=0, sticky="w", pady=(0, 5))
entrada_carpeta = ttk.Entry(frame, width=50)
entrada_carpeta.grid(row=3, column=0, padx=(0, 10), pady=(0, 15), sticky="we")
btn_buscar_carpeta = ttk.Button(
    frame, text="Buscar Carpeta", command=seleccionar_carpeta
)
btn_buscar_carpeta.grid(row=3, column=1, pady=(0, 15))

# Separador visual
ttk.Separator(frame, orient="horizontal").grid(
    row=4, column=0, columnspan=2, sticky="we", pady=10
)

# Botón de Acción Principal
btn_ejecutar = ttk.Button(
    frame, text="¡Unir PDFs!", command=iniciar_fusion, style="Accent.TButton"
)
btn_ejecutar.grid(row=5, column=0, columnspan=2, pady=(10, 0))

# Etiqueta de Estado en la parte inferior
lbl_estado = tk.Label(frame, text="", font=("Arial", 9, "italic"))
lbl_estado.grid(row=6, column=0, columnspan=2, pady=(5, 0))

# Hacer que la columna de texto se estire si es necesario
frame.columnconfigure(0, weight=1)

# Arrancar la aplicación
ventana.mainloop()
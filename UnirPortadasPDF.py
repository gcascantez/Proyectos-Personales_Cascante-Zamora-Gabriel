import os
from pypdf import PdfWriter

def unir_portada_con_nombre_original(pdf_principal, carpeta_fuente):
    # 1. OBTENER LA RUTA AUTOMÁTICA A "DOWNLOADS"
    # os.path.expanduser("~") encuentra la carpeta de tu usuario (ej. C:/Users/TuUsuario)
    carpeta_usuario = os.path.expanduser("~")
    carpeta_salida = os.path.join(carpeta_usuario, "Downloads", "resultados_combinados")
    
    os.makedirs(carpeta_salida, exist_ok=True)
    print(f"Los archivos se guardarán en: {carpeta_salida}")
    
    for archivo in os.listdir(carpeta_fuente):
        if archivo.endswith(".pdf") and archivo != os.path.basename(pdf_principal):
            ruta_pdf_secundario = os.path.join(carpeta_fuente, archivo)
            
            fusionador = PdfWriter()
            fusionador.append(pdf_principal)
            fusionador.append(ruta_pdf_secundario)
            
            ruta_salida = os.path.join(carpeta_salida, archivo)
            with open(ruta_salida, "wb") as archivo_final:
                fusionador.write(archivo_final)
                
            fusionador.close()
            print(f"Procesado con éxito: {archivo}")

# =====================================================================
# 2. AQUÍ CONFIGURAS TU PDF PRINCIPAL Y TU CARPETA DE ORIGEN
# =====================================================================

# Reemplaza lo que está entre comillas con las rutas reales de tu computadora:
pdf_unico = r"C:\Users\gcasc\OneDrive - Estudiantes ITCR\UUUU\IS 2026\Asistencia DT\Planeamiento actividades\Actividad 5\2026_IS_DT_PS5_RUBRICA.pdf"
carpeta_con_pdfs = r"C:\Users\gcasc\OneDrive - Estudiantes ITCR\UUUU\IS 2026\Asistencia DT\Revisiones de prácticas supervisadas\PS5\G21\Entregas Estudiantes" 

# Ejecutar la función
unir_portada_con_nombre_original(pdf_unico, carpeta_con_pdfs)

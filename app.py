import streamlit as st
import io
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

from extractor import ExtractorInmobiliario
from motor_acm import MotorACM
import pipeline_db

# Configuración inicial
st.set_page_config(page_title="Metabuscador ACM Profesional", layout="wide")
pipeline_db.inicializar_db()

st.title("📊 Metabuscador Inmobiliario - Automatización ACM")
st.markdown("---")

# 1. ENTRADA DE DATOS
with st.sidebar:
    st.header("Configuración del Inmueble")
    municipio = st.selectbox("Municipio", pipeline_db.obtener_municipios_totales())
    barrio = st.selectbox("Barrio / Sector", pipeline_db.obtener_barrios_por_municipio(municipio))
    rph = st.radio("¿Propiedad Horizontal?", ["SÍ", "NO"])
    area_obj = st.number_input("Área de Referencia (m²)", value=100.0)

# 2. SECCIÓN DE BÚSQUEDA Y AUTOMATIZACIÓN
st.subheader("Búsqueda de Ofertas de Mercado")
extractor = ExtractorInmobiliario()
enlaces = extractor.obtener_enlaces_veridicos(municipio, barrio, rph)

st.write("Selecciona un portal para auditar ofertas reales y cargarlas:")
for nombre, link in enlaces:
    st.markdown(f"- [{nombre}]({link})")

st.markdown("### 3. Carga de Muestras Verificadas")
with st.expander("Ingreso masivo de datos extraídos (Precios y Áreas Reales)"):
    if "muestras" not in st.session_state: st.session_state.muestras = []
    
    col1, col2, col3 = st.columns(3)
    p_in = col1.number_input("Precio ($)", step=1000000)
    a_in = col2.number_input("Área (m²)", step=0.1)
    l_in = col3.text_input("Link de la muestra")
    
    if st.button("Guardar Muestra en Metabuscador"):
        nueva_muestra = {
            "id_portal": f"AUTO-{len(st.session_state.muestras)}",
            "portal": "Auditoría Manual", "link": l_in, "municipio": municipio,
            "barrio": barrio, "precio_oferta": p_in, "area_construida": a_in if rph=="SÍ" else 0,
            "area_terreno": a_in if rph=="NO" else 0, "edad_construccion": 10,
            "fn": 0.95, "f_ubicacion": 1.0, "f_edad": 1.0, "f_caracteristicas": 1.0
        }
        st.session_state.muestras.append(nueva_muestra)
        pipeline_db.guardar_muestras_upsert([nueva_muestra])

# 3. PROCESAMIENTO ESTADÍSTICO Y EXCEL
if st.button("🚀 Ejecutar Homologación y Generar Dictamen"):
    if len(st.session_state.muestras) < 3:
        st.warning("Se requieren al menos 3 muestras para el control estadístico.")
    else:
        motor = MotorACM()
        valores = motor.procesar_homogenizacion(st.session_state.muestras, rph)
        promedio, desv, cv, asimetria, lim_sup, lim_inf, aprobado = motor.analizar_estadistica_igac(valores)
        
        st.metric("Valor M² Adoptado", f"${promedio:,.0f}")
        st.metric("Coeficiente de Variación", f"{cv*100:.2f}%")
        
        if aprobado:
            st.success("Criterio IGAC Cumplido (CV <= 15%)")
            # AQUÍ LLAMAS A TU FUNCIÓN DE EXCEL (generar_excel_rph_si/no)
            st.balloons()
        else:
            st.error("CV fuera de rango. Requiere depuración de muestras.")
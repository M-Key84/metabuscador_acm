import streamlit as st
import io
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

from extractor import ExtractorInmobiliario
from motor_acm import MotorACM
import pipeline_db

st.set_page_config(page_title="Portal Metabuscador ACM Nacional", layout="centered")

st.title("Plataforma Inmobiliaria - Motor ACM Nacional")
st.subheader("Automatización de Dictámenes Técnicos (Resolución IGAC 620 de 2008)")
st.markdown("---")

# Inicializar la base de datos relacional y descargar municipios del DANE si es primera vez
pipeline_db.inicializar_db()

if "procesado" not in st.session_state:
    st.session_state.procesado = False
    st.session_state.muestras = []
    st.session_state.valores_m2 = []
    st.session_state.media = 0.0
    st.session_state.desv = 0.0
    st.session_state.cv = 0.0
    st.session_state.aprobado = False
    st.session_state.datos_inmueble = {}

st.markdown("### 🔍 Parámetros de Consulta del Inmueble Objetivo")

col_adm1, col_adm2 = st.columns(2)
with col_adm1:
    propietario = st.text_input("Nombre del Propietario / Solicitante", "Manuel Alejandro Kock Mora")
with col_adm2:
    matricula = st.text_input("Número de Matrícula Inmobiliaria", "012-46368")

# DROPDOWN INTELIGENTE CON COBERTURA DE TODA COLOMBIA (Vía DANE)
col_geo1, col_geo2 = st.columns(2)
with col_geo1:
    lista_municipios_colombia = pipeline_db.obtainer_municipios_totales()
    # Si la base de datos falló por red, usamos la lista de control
    if not lista_municipios_colombia:
        lista_municipios_colombia = ["Medellín", "Bello", "Girardota", "Bogotá", "Cali", "Barranquilla"]
        
    municipio = st.selectbox("Seleccione el Municipio (Catálogo Oficial DANE)", lista_municipios_colombia)
with col_geo2:
    barrio = st.text_input("Escriba el Barrio o Sector Oficial", "Ciudad Jardín")

st.markdown("#### Especificaciones Físicas del Predio")
col_fiz1, col_fiz2 = st.columns(2)
with col_fiz1:
    rph = st.radio("¿Sometido a Régimen de Propiedad Horizontal (RPH)?", ["SÍ", "NO"])
with col_fiz2:
    area_construida = st.number_input("Área Construida Total (m²)", min_value=5.0, value=120.0, step=1.0)

if rph == "NO":
    area_terreno = st.number_input("Área de Terreno Lote (m²)", min_value=10.0, value=855.30, step=0.1)
else:
    area_terreno = 0.0

st.markdown("---")

def fabricar_excel_con_formulas_vivas(datos_obj, muestras, valores_m2):
    wb = openpyxl.Workbook()
    navy_header = "1B365D"
    navy_light = "F2F4F8"
    white = "FFFFFF"
    
    font_title = Font(name="Arial", size=12, bold=True, color=navy_header)
    font_header = Font(name="Arial", size=10, bold=True, color=white)
    font_bold = Font(name="Arial", size=10, bold=True)
    font_regular = Font(name="Arial", size=10)
    fill_header = PatternFill(start_color=navy_header, end_color=navy_header, fill_type="solid")
    fill_zebra = PatternFill(start_color=navy_light, end_color=navy_light, fill_type="solid")
    fill_accent = PatternFill(start_color="E6F0FA", end_color="E6F0FA", fill_type="solid")
    thin_border = Border(left=Side(style='thin', color='D3D3D3'), right=Side(style='thin', color='D3D3D3'),
                         top=Side(style='thin', color='D3D3D3'), bottom=Side(style='thin', color='D3D3D3'))

    ws1 = wb.active
    ws1.title = "1. Inmueble Objetivo"
    ws1.views.sheetView[0].showGridLines = True
    ws1["A2"] = "INFORME TÉCNICO - VARIABLES DEL INMUEBLE OBJETIVO"
    ws1["A2"].font = font_title
    
    headers_ws1 = ["Parámetro Evaluado", "Valor Indexado en Sistema"]
    ws1.append([])
    ws1.append([])
    ws1.append(headers_ws1)
    
    for c in [1, 2]:
        cell = ws1.cell(row=5, column=c)
        cell.font = font_header
        cell.fill = fill_header
        cell.alignment = Alignment(horizontal="center")

    variables_mapeadas = [
        ("PROPIETARIO", datos_obj["propietario"]),
        ("MATRÍCULA INMOBILIARIA", datos_obj["matricula"]),
        ("MUNICIPIO", datos_obj["municipio"]),
        ("BARRIO", datos_obj["barrio"]),
        ("SOMETIDO A RPH", datos_obj["rph"]),
        ("ÁREA CONSTRUIDA", datos_obj["area_construida"]),
        ("ÁREA TERRENO LOTE", datos_obj["area_terreno"])
    ]

    for i, (campo, val) in enumerate(variables_mapeadas, start=6):
        ws1.cell(row=i, column=1, value=campo).font = font_regular
        c_val = ws1.cell(row=i, column=2, value=val)
        c_val.font = font_bold
        ws1.cell(row=i, column=1).border = thin_border
        c_val.border = thin_border
        if isinstance(val, (int, float)):
            c_val.number_format = "#,##0.00"
            c_val.alignment = Alignment(horizontal="right")

    ws2 = wb.create_sheet(title="2. Matriz de Homologación")
    ws2.views.sheetView[0].showGridLines = True
    ws2["A2"] = "ESTUDIO DE MERCADO - HOMOLOGACIÓN DE CELDAS DINÁMICAS"
    ws2["A2"].font = font_title
    
    headers_ws2 = ["Muestra", "Portal Fuente", "Precio Oferta (COP)", "Factor Neg. (Fn)", "Precio Depurado", "Área", "Valor M² Unitario"]
    ws2.append([])
    ws2.append([])
    ws2.append(headers_ws2)
    
    for col_idx, h in enumerate(headers_ws2, 1):
        cell = ws2.cell(row=5, column=col_idx)
        cell.font = font_header
        cell.fill = fill_header
        cell.alignment = Alignment(horizontal="center")

    fila_inicio = 6
    for idx, m in enumerate(muestras):
        f = fila_inicio + idx
        r_fill = fill_zebra if f % 2 == 0 else PatternFill(fill_type=None)
        
        ws2.cell(row=f, column=1, value=f"Muestra {idx+1}").alignment = Alignment(horizontal="center")
        ws2.cell(row=f, column=2, value=m["portal"])
        ws2.cell(row=f, column=3, value=m["precio_oferta"]).number_format = "$#,##0"
        ws2.cell(row=f, column=4, value=0.95).number_format = "0.00"
        ws2.cell(row=f, column=5, value=f"=C{f}*D{f}").number_format = "$#,##0"
        
        area_val = m["area_construida"] if datos_obj["rph"] == "SÍ" else m["area_terreno"]
        ws2.cell(row=f, column=6, value=area_val).number_format = "#,##0.00"
        ws2.cell(row=f, column=7, value=f"=E{f}/F{f}").number_format = "$#,##0"
        
        for col_c in range(1, 8):
            cell = ws2.cell(row=f, column=col_c)
            cell.border = thin_border
            if r_fill.fill_type: cell.fill = r_fill

    fila_fin = fila_inicio + len(muestras) - 1
    fila_prom = fila_fin + 2
    
    ws2.cell(row=fila_prom, column=1, value="PROMEDIO").font = font_bold
    ws2.cell(row=fila_prom, column=7, value=f"=AVERAGE(G{fila_inicio}:G{fila_fin})").font = font_bold
    ws2.cell(row=fila_prom, column=7).number_format = "$#,##0"

    ws3 = wb.create_sheet(title="3. Análisis Estadístico IGAC")
    ws3.views.sheetView[0].showGridLines = True
    ws3["A2"] = "DICTAMEN FINAL DE LIQUIDACIÓN CATASTRAL EN VIVO"
    ws3["A2"].font = font_title
    
    ws3["A5"] = "Parámetro Evaluado"
    ws3["B5"] = "Fórmula Operativa / Valor"
    ws3["C5"] = "Requisito Legal Res. 620"
    
    for c in [1, 2, 3]:
        cell = ws3.cell(row=5, column=c)
        cell.font = font_header
        cell.fill = fill_header
        cell.alignment = Alignment(horizontal="center")

    ws3["A6"] = "Promedio del Valor M² Homogenizado:"
    ws3["B6"] = f"='2. Matriz de Homologación'!G{fila_prom}"
    ws3["B6"].number_format = "$#,##0"
    ws3["B6"].font = font_bold
    
    ws3["A7"] = "Desviación Estándar Muestral (σ):"
    ws3["B7"] = f"=STDEV.S('2. Matriz de Homologación'!G{fila_inicio}:G{fila_fin})"
    ws3["B7"].number_format = "$#,##0"
    
    ws3["A8"] = "Coeficiente de Variación (CV):"
    ws3["B8"] = "=B7/B6"
    ws3["B8"].number_format = "0.00%"
    ws3["B8"].font = font_bold
    ws3["C8"] = "OBLIGATORIO: Máximo 15.00%"
    ws3["C8"].font = font_bold
    
    ws3["A10"] = "Validación Jurídica del Estudio:"
    ws3["B10"] = '=IF(B8<=0.15,"ACEPTADO (Estudio Estable)","RECHAZADO POR ALTA DISPERSIÓN")'
    ws3["B10"].font = font_bold
    
    ws3["A13"] = "Área Total a Liquidar del Objetivo:"
    ws3["B13"] = "='1. Inmueble Objetivo'!B11" if datos_obj["rph"] == "SÍ" else "='1. Inmueble Objetivo'!B12"
    ws3["B13"].number_format = "#,##0.00"
    
    ws3["A14"] = "VALOR COMERCIAL ESTIMADO FINAL:"
    ws3["B14"] = "=B6*B13"
    ws3["B14"].number_format = "$#,##0"
    ws3["B14"].font = Font(name="Arial", size=11, bold=True, color=navy_header)
    ws3["B14"].fill = fill_accent
    ws3["B14"].border = Border(bottom=Side(style='medium', color=navy_header))

    for r in [6, 7, 8, 10, 13, 14]:
        for col_c in range(1, 4):
            ws3.cell(row=r, column=col_c).border = thin_border

    for ws in [wb[sn] for sn in wb.sheetnames]:
        for col in ws.columns:
            max_len = max(len(str(cell.value or '')) for cell in col)
            col_letter = get_column_letter(col[0].column)
            ws.column_dimensions[col_letter].width = max(max_len + 3, 15)
            
    ws3.column_dimensions["A"].width = 35
    ws3.column_dimensions["C"].width = 28

    buffer = io.BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    return buffer

if st.button("🚀 Consultar Metabuscador y Procesar Homologación", use_container_width=True):
    st.session_state.datos_inmueble = {
        "propietario": propietario,
        "matricula": matricula,
        "municipio": municipio,
        "barrio": barrio,
        "rph": rph,
        "area_construida": area_construida,
        "area_terreno": area_terreno
    }
    
    area_referencia = area_construida if rph == "SÍ" else area_terreno
    st.session_state.muestras = pipeline_db.consultar_muestras_validas(municipio, barrio, area_referencia, rph)
    
    if len(st.session_state.muestras) == 0:
        extractor = ExtractorInmobiliario()
        muestras_internet = extractor.raspar_portal_simulado(municipio, barrio, rph)
        pipeline_db.guardar_muestras_upsert(muestras_internet)
        st.session_state.muestras = pipeline_db.consultar_muestras_validas(municipio, barrio, area_referencia, rph)

    motor = MotorACM()
    st.session_state.valores_m2 = motor.procesar_homogenizacion(st.session_state.muestras, rph)
    st.session_state.media, st.session_state.desv, st.session_state.cv, st.session_state.aprobado = motor.analizar_estadistica_igac(st.session_state.valores_m2)
    st.session_state.procesado = True

if st.session_state.procesado:
    st.markdown("---")
    st.markdown("### 📊 Tablero Analítico Métrico Temporal")
    
    col_m1, col_m2 = st.columns(2)
    col_m1.metric("Valor Promedio por M²", f"${st.session_state.media:,.2f}")
    col_m2.metric("Coeficiente de Variación (CV)", f"{st.session_state.cv*100:.2f}%")
    
    if st.session_state.aprobado:
        st.success("✔️ Control Calidad: Muestra Consistente. Cumple la restricción legal (CV <= 15%).")
    else:
        st.error("❌ Alerta de Dispersión: El CV del mercado supera el 15% normativo. Los datos de la zona están desalineados.")
        
    excel_final = fabricar_excel_con_formulas_vivas(
        st.session_state.datos_inmueble, 
        st.session_state.muestras, 
        st.session_state.valores_m2
    )
    
    st.download_button(
        label="📥 Descargar Dictamen Técnico Completo (Excel con Fórmulas)",
        data=excel_final,
        file_name=f"ACM_AUTOMATICO_{st.session_state.datos_inmueble['barrio']}_{st.session_state.datos_inmueble['municipio']}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True
    )
import streamlit as st
import io
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

from extractor import ExtractorInmobiliario
from motor_acm import MotorACM
import pipeline_db

st.set_page_config(page_title="Metabuscador ACM Profesional (Valle de Aburrá)", layout="centered")

st.title("Plataforma Inmobiliaria - Valle de Aburrá")
st.subheader("Dictámenes Técnicos Automatizados conforme a Resolución IGAC 620 de 2008")
st.markdown("---")

pipeline_db.inicializar_db()

if "procesado" not in st.session_state:
    st.session_state.procesado = False
    st.session_state.muestras = []
    st.session_state.valores_m2 = []
    st.session_state.media = 0.0
    st.session_state.desv = 0.0
    st.session_state.cv = 0.0
    st.session_state.asimetria = 0.0
    st.session_state.lim_sup = 0.0
    st.session_state.lim_inf = 0.0
    st.session_state.aprobado = False
    st.session_state.datos_inmueble = {}

st.markdown("### 🔍 Parámetros del Inmueble Objetivo")

# --- Datos administrativos ---
col_adm1, col_adm2 = st.columns(2)
with col_adm1:
    propietario = st.text_input("Nombre del Propietario / Solicitante", "Manuel Alejandro Kock Mora")
with col_adm2:
    matricula = st.text_input("Número de Matrícula Inmobiliaria", "012-46368")

# --- Ubicación ---
col_geo1, col_geo2 = st.columns(2)
with col_geo1:
    lista_municipios = pipeline_db.obtener_municipios_totales()
    municipio = st.selectbox("Seleccione el Municipio", lista_municipios)
with col_geo2:
    lista_barrios = pipeline_db.obtener_barrios_por_municipio(municipio)
    barrio = st.selectbox("Seleccione el Barrio, Sector o Corregimiento", lista_barrios)

# --- Tipo de zona y RPH ---
col_zona, col_rph = st.columns(2)
with col_zona:
    tipo_zona = st.radio("Tipo de Zona", ["Urbana", "Rural"])
with col_rph:
    rph = st.radio("¿Sometido a Régimen de Propiedad Horizontal (RPH)?", ["SÍ", "NO"])

st.markdown("#### Especificaciones Físicas del Predio")

# --- Áreas ---
col_fiz1, col_fiz2 = st.columns(2)
with col_fiz1:
    area_construida = st.number_input("Área Construida (m²)", min_value=5.0, value=120.0, step=1.0)
    area_libre = st.number_input("Área Libre (m²)", min_value=0.0, value=0.0, step=0.1)
with col_fiz2:
    area_total = st.number_input("Área Total (m²)", min_value=5.0, value=120.0, step=1.0)
    piso = st.number_input("Piso", min_value=1, value=1, step=1)

# --- Complementos ---
col_comp1, col_comp2 = st.columns(2)
with col_comp1:
    garaje = st.checkbox("Garaje")
with col_comp2:
    patio = st.number_input("Patio (m²)", min_value=0.0, value=0.0, step=0.5)
terraza = st.number_input("Terraza (m²)", min_value=0.0, value=0.0, step=0.5)

# Si no es RPH, pedimos área de terreno (fundamental para el avalúo)
if rph == "NO":
    area_terreno = st.number_input("Área de Terreno Lote (m²)", min_value=10.0, value=area_total, step=0.1)
else:
    area_terreno = 0.0

st.markdown("---")

def seleccionar_top5_por_area(muestras, area_ref, es_rph):
    """Ordena las muestras por cercanía de área (construida si RPH, terreno si no) y devuelve las 5 mejores."""
    col_area = "area_construida" if es_rph == "SÍ" else "area_terreno"
    validas = [m for m in muestras if m.get(col_area, 0) > 0]
    if not validas:
        return muestras[:5]
    validas.sort(key=lambda x: abs(x[col_area] - area_ref))
    return validas[:5]

def fabricar_excel_con_formulas_vivas(datos_obj, muestras):
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

    # ========== PESTAÑA 1: FICHA DEL INMUEBLE OBJETIVO ==========
    ws1 = wb.active
    ws1.title = "1. Ficha Inmueble Objetivo"
    ws1.views.sheetView[0].showGridLines = True
    ws1["A2"] = "INFORME DE VALUACIÓN INMOBILIARIA - METABUSCADOR ACM"
    ws1["A2"].font = font_title
    ws1["A3"] = "Cumplimiento Normativo: Resolución IGAC 620 de 2008"
    ws1["A3"].font = Font(name="Arial", size=10, italic=True)
    
    headers_ws1 = ["Variable Requerida", "Valor / Especificación"]
    ws1.append([])
    ws1.append([])
    ws1.append(headers_ws1)
    
    for c in [1, 2]:
        cell = ws1.cell(row=5, column=c)
        cell.font = font_header
        cell.fill = fill_header
        cell.alignment = Alignment(horizontal="center")

    # Lista de variables con Área de Terreno incluida (necesaria para liquidación)
    variables_mapeadas = [
        ("Propietario del Inmueble", datos_obj["propietario"]),
        ("Matrícula Inmobiliaria", datos_obj["matricula"]),
        ("Municipio", datos_obj["municipio"]),
        ("Barrio / Sector / Corregimiento", datos_obj["barrio"]),
        ("Tipo de Zona", datos_obj["tipo_zona"]),
        ("Sometido a RPH", datos_obj["rph"]),
        ("Área Construida", datos_obj["area_construida"]),
        ("Área de Terreno", datos_obj.get("area_terreno", 0)),   # <-- nuevo campo
        ("Área Libre", datos_obj.get("area_libre", 0)),
        ("Área Total", datos_obj.get("area_total", 0)),
        ("Piso", datos_obj.get("piso", "")),
        ("Garaje", "Sí" if datos_obj.get("garaje") else "No"),
        ("Patio (m²)", datos_obj.get("patio", 0)),
        ("Terraza (m²)", datos_obj.get("terraza", 0))
    ]

    for i, (campo, val) in enumerate(variables_mapeadas, start=6):
        ws1.cell(row=i, column=1, value=campo).font = font_regular
        c_val = ws1.cell(row=i, column=2, value=val)
        c_val.font = font_bold
        ws1.cell(row=i, column=1).border = thin_border
        c_val.border = thin_border

    # ========== PESTAÑA 2: MATRIZ DE HOMOLOGACIÓN (5 muestras) ==========
    ws2 = wb.create_sheet(title="Homologacion")
    ws2.views.sheetView[0].showGridLines = True
    ws2["A2"] = "MATRIZ DE HOMOLOGACIÓN Y AJUSTE DE MUESTRAS EN VIVO"
    ws2["A2"].font = font_title
    
    headers_ws2 = [
        "Muestra", "Portal Fuente", "Link", "Precio Oferta (COP)", "Factor Negoc. (Fn)", 
        "Precio Depurado (COP)", "Área (m²)", "Valor M² Depurado", 
        "F. Ubicación", "F. Edad", "F. Características", "Factor Resultante (Fr)", "Valor M² Homogenizado (COP)"
    ]
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
        # Hipervínculo funcional
        link_cell = ws2.cell(row=f, column=3, value="Ver oferta")
        link_cell.hyperlink = m.get("link", "#")
        link_cell.font = Font(name="Arial", size=10, color="0563C1", underline="single")
        
        ws2.cell(row=f, column=4, value=m["precio_oferta"]).number_format = "#,##0"
        ws2.cell(row=f, column=5, value=m.get("fn", 0.95)).number_format = "0.00"
        # Fórmulas en inglés
        ws2.cell(row=f, column=6, value=f"=D{f}*E{f}").number_format = "#,##0"
        area_val = m["area_construida"] if datos_obj["rph"] == "SÍ" else m["area_terreno"]
        ws2.cell(row=f, column=7, value=area_val).number_format = "#,##0.00"
        ws2.cell(row=f, column=8, value=f"=F{f}/G{f}").number_format = "#,##0"
        
        ws2.cell(row=f, column=9, value=m.get("f_ubicacion", 1.0)).number_format = "0.00"
        ws2.cell(row=f, column=10, value=m.get("f_edad", 1.0)).number_format = "0.00"
        ws2.cell(row=f, column=11, value=m.get("f_caracteristicas", 1.0)).number_format = "0.00"
        
        ws2.cell(row=f, column=12, value=f"=I{f}*J{f}*K{f}").number_format = "0.00"
        ws2.cell(row=f, column=13, value=f"=H{f}*L{f}").number_format = "#,##0"
        
        for col_c in range(1, 14):
            cell = ws2.cell(row=f, column=col_c)
            cell.border = thin_border
            if r_fill.fill_type: cell.fill = r_fill

    fila_fin = fila_inicio + len(muestras) - 1
    fila_prom = fila_fin + 2
    
    ws2.cell(row=fila_prom, column=1, value="PROMEDIO").font = font_bold
    ws2.cell(row=fila_prom, column=13, value=f"=AVERAGE(M{fila_inicio}:M{fila_fin})").font = font_bold
    ws2.cell(row=fila_prom, column=13).number_format = "#,##0"

    # ========== PESTAÑA 3: ANÁLISIS ESTADÍSTICO (15%) ==========
    ws3 = wb.create_sheet(title="3. Análisis Estadístico IGAC")
    ws3.views.sheetView[0].showGridLines = True
    ws3["A2"] = "CÁLCULOS ESTADÍSTICOS Y CÁLCULO DE VALOR COMERCIAL"
    ws3["A2"].font = font_title
    ws3["A3"] = "Control de dispersión de la muestra e inferencia del valor"
    ws3["A3"].font = Font(name="Arial", size=10, italic=True)
    
    ws3["A5"] = "Parámetro Estadístico"
    ws3["B5"] = "Fórmula / Valor"
    ws3["C5"] = "Criterio de Aceptación"
    
    for c in [1, 2, 3]:
        cell = ws3.cell(row=5, column=c)
        cell.font = font_header
        cell.fill = fill_header
        cell.alignment = Alignment(horizontal="center")

    # Constantes en celdas ocultas (15%)
    ws3["D10"] = 1.15
    ws3["D10"].number_format = "0.000"
    ws3["D11"] = 0.85
    ws3["D11"].number_format = "0.000"

    ws3["A6"] = "Promedio del Valor M² Homogenizado"
    ws3["B6"] = f"=Homologacion!M{fila_prom}"
    ws3["B6"].number_format = "#,##0"
    ws3["B6"].font = font_bold
    ws3["C6"] = "Base para la liquidación del metro cuadrado"
    
    ws3["A7"] = "Desviación Estándar de la Muestra (σ)"
    ws3["B7"] = f"=STDEV.S(Homologacion!M{fila_inicio}:M{fila_fin})"
    ws3["B7"].number_format = "#,##0"
    ws3["C7"] = "Mide el grado de dispersión de los precios de los portales"
    
    ws3["A8"] = "Coeficiente de Variación (CV)"
    ws3["B8"] = "=B7/B6"
    ws3["B8"].number_format = "0.00%"
    ws3["B8"].font = font_bold
    ws3["C8"] = "CRITERIO DE ALTA PRECISIÓN: Debe ser menor o igual al 15.00%"
    
    ws3["A9"] = "Coeficiente de Asimetría"
    ws3["B9"] = f"=SKEW(Homologacion!M{fila_inicio}:M{fila_fin})"
    ws3["B9"].number_format = "0.00"
    ws3["C9"] = "Mide la tendencia de sesgo de las ofertas"

    ws3["A10"] = "Límite Superior (15%)"
    ws3["B10"] = "=B6*D10"
    ws3["B10"].number_format = "#,##0"
    
    ws3["A11"] = "Límite Inferior (15%)"
    ws3["B11"] = "=B6*D11"
    ws3["B11"].number_format = "#,##0"

    ws3["A13"] = "LIQUIDACIÓN DEL VALOR COMERCIAL CONFORME A LA RESOLUCIÓN"
    ws3["A13"].font = font_bold
    
    ws3["A15"] = "Área del Inmueble Objetivo a Liquidar"
    # Área Construida está en B12, Área de Terreno en B13
    ws3["B15"] = "='1. Ficha Inmueble Objetivo'!B12" if datos_obj["rph"] == "SÍ" else "='1. Ficha Inmueble Objetivo'!B13"
    ws3["B15"].number_format = "#,##0.00"
    ws3["C15"] = "Metros cuadrados tomados del informe físico"
    
    ws3["A16"] = "Valor por M² Homogenizado Adoptado"
    ws3["B16"] = "=B6"
    ws3["B16"].number_format = "#,##0"
    ws3["B16"].font = font_bold
    
    ws3["A17"] = "VALOR COMERCIAL TOTAL ESTIMADO"
    ws3["B17"] = "=B15*B16"
    ws3["B17"].number_format = "$#,##0"
    ws3["B17"].font = Font(name="Arial", size=11, bold=True, color=navy_header)
    ws3["B17"].fill = fill_accent
    ws3["B17"].border = Border(bottom=Side(style='medium', color=navy_header))
    ws3["C17"] = "Resultado Final del Dictamen Técnico"

    for r in [6, 7, 8, 9, 10, 11, 15, 16, 17]:
        for col_c in range(1, 4):
            ws3.cell(row=r, column=col_c).border = thin_border

    ws3.column_dimensions["D"].hidden = True

    for ws in [ws1, ws2, ws3]:
        for col in ws.columns:
            max_len = max(len(str(cell.value or '')) for cell in col)
            col_letter = get_column_letter(col[0].column)
            ws.column_dimensions[col_letter].width = max(max_len + 3, 15)
            
    ws3.column_dimensions["A"].width = 38
    ws3.column_dimensions["C"].width = 50

    buffer = io.BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    return buffer

# --- Botón de procesamiento ---
if st.button("🚀 Consultar Metabuscador y Procesar Homologación", use_container_width=True):
    st.session_state.datos_inmueble = {
        "propietario": propietario,
        "matricula": matricula,
        "municipio": municipio,
        "barrio": barrio,
        "tipo_zona": tipo_zona,
        "rph": rph,
        "area_construida": area_construida,
        "area_libre": area_libre,
        "area_total": area_total,
        "piso": piso,
        "garaje": garaje,
        "patio": patio,
        "terraza": terraza,
        "area_terreno": area_terreno
    }
    
    area_referencia = area_construida if rph == "SÍ" else area_terreno
    st.session_state.muestras = pipeline_db.consultar_muestras_validas(municipio, barrio, area_referencia, rph)
    
    if len(st.session_state.muestras) == 0:
        extractor = ExtractorInmobiliario()
        es_rural = (tipo_zona == "Rural")
        muestras_internet = extractor.raspar_portal_real(municipio, barrio, rph, area_referencia, es_rural)
        pipeline_db.guardar_muestras_upsert(muestras_internet)
        st.session_state.muestras = pipeline_db.consultar_muestras_validas(municipio, barrio, area_referencia, rph)

    motor = MotorACM()
    st.session_state.valores_m2 = motor.procesar_homogenizacion(st.session_state.muestras, rph)
    st.session_state.media, st.session_state.desv, st.session_state.cv, st.session_state.asimetria, st.session_state.lim_sup, st.session_state.lim_inf, st.session_state.aprobado = motor.analizar_estadistica_igac(st.session_state.valores_m2)
    
    top5 = seleccionar_top5_por_area(st.session_state.muestras, area_referencia, rph)
    st.session_state.top5_muestras = top5
    st.session_state.procesado = True

if st.session_state.procesado:
    st.markdown("---")
    st.markdown("### 📊 Tablero Analítico Control 15% Pro")
    
    col_m1, col_m2, col_m3 = st.columns(3)
    col_m1.metric("Promedio Homogenizado M²", f"${st.session_state.media:,.2f}")
    col_m2.metric("Coeficiente de Variación (CV)", f"{st.session_state.cv*100:.2f}%")
    col_m3.metric("Coeficiente de Asimetría (SKEW)", f"{st.session_state.asimetria:.4f}")
    
    col_lim1, col_lim2 = st.columns(2)
    col_lim1.metric("Límite Inferior (15%)", f"${st.session_state.lim_inf:,.2f}")
    col_lim2.metric("Límite Superior (15%)", f"${st.session_state.lim_sup:,.2f}")
    
    if st.session_state.aprobado:
        st.success("✔️ Muestra Consistente de Alta Precisión. Cumple el criterio IGAC (CV ≤ 15%).")
    else:
        st.error("❌ Muestra Rechazada por Alta Dispersión. Supera el límite de control del 15%.")
        
    excel_final = fabricar_excel_con_formulas_vivas(st.session_state.datos_inmueble, st.session_state.top5_muestras)
    
    st.download_button(
        label="📥 Descargar Dictamen Técnico Oficial (Fórmulas Excel Vivas)",
        data=excel_final,
        file_name=f"DICTAMEN_PRO_{st.session_state.datos_inmueble['barrio']}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True
    )
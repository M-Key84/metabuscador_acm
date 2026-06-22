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
    st.session_state.top5_muestras = []
    st.session_state.calc_fitto = {}

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

# --- Datos para Fitto Corvini (solo si NO es RPH) ---
if rph == "NO":
    area_terreno = st.number_input("Área de Terreno Lote (m²)", min_value=10.0, value=area_total, step=0.1)
    st.markdown("#### Datos de la construcción (Fitto Corvini)")
    edad_const = st.number_input("Edad de la construcción (años)", min_value=0, value=35, step=1)
    conservacion = st.selectbox("Estado de conservación", ["Buena", "Regular", "Mala"])
    costo_reposicion_m2 = st.number_input("Costo reposición M2 ($)", min_value=500000, value=3435827, step=10000)
else:
    area_terreno = 0.0
    edad_const = 0
    conservacion = ""
    costo_reposicion_m2 = 0

st.markdown("---")

# --- Función Fitto Corvini ---
def fitto_corvini(area, edad, vida_util, conservacion, costo_m2):
    clase = {"Buena": 3, "Regular": 4, "Mala": 5}.get(conservacion, 3)
    edad_pct = (edad / vida_util) * 100
    if edad_pct <= 5:
        coef = 0.05
    elif edad_pct <= 10:
        coef = 0.10
    elif edad_pct <= 20:
        coef = 0.20 + (clase - 3) * 0.05
    elif edad_pct <= 30:
        coef = 0.30 + (clase - 3) * 0.10
    elif edad_pct <= 50:
        coef = 0.50 + (clase - 3) * 0.15
    else:
        coef = 0.70 + (clase - 3) * 0.20
    coef = min(coef, 0.90)
    valor_depreciado_m2 = costo_m2 * (1 - coef)
    valor_total_construccion = valor_depreciado_m2 * area
    return {
        "coef": coef,
        "valor_depreciado_m2": valor_depreciado_m2,
        "valor_total_construccion": valor_total_construccion
    }

# --- Top 5 por área ---
def seleccionar_top5_por_area(muestras, area_ref, es_rph):
    col_area = "area_construida" if es_rph == "SÍ" else "area_terreno"
    validas = [m for m in muestras if m.get(col_area, 0) > 0]
    if not validas:
        return muestras[:5]
    validas.sort(key=lambda x: abs(x[col_area] - area_ref))
    return validas[:5]

# ==================== GENERACIÓN DEL EXCEL SEGÚN RPH ====================
def generar_excel_rph_si(datos_obj, muestras):
    """Plantilla para apartamentos (RPH=SÍ): Homologación + Análisis Estadístico."""
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

    # Hoja 1: Ficha
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

    vars_ficha = [
        ("Propietario del Inmueble", datos_obj["propietario"]),
        ("Matrícula Inmobiliaria", datos_obj["matricula"]),
        ("Municipio", datos_obj["municipio"]),
        ("Barrio / Sector / Corregimiento", datos_obj["barrio"]),
        ("Tipo de Zona", datos_obj["tipo_zona"]),
        ("Sometido a RPH", datos_obj["rph"]),
        ("Área Construida", datos_obj["area_construida"]),
        ("Área Total", datos_obj.get("area_total", 0)),
        ("Piso", datos_obj.get("piso", "")),
        ("Garaje", "Sí" if datos_obj.get("garaje") else "No"),
        ("Patio (m²)", datos_obj.get("patio", 0)),
        ("Terraza (m²)", datos_obj.get("terraza", 0))
    ]
    for i, (campo, val) in enumerate(vars_ficha, start=6):
        ws1.cell(row=i, column=1, value=campo).font = font_regular
        c_val = ws1.cell(row=i, column=2, value=val)
        c_val.font = font_bold
        ws1.cell(row=i, column=1).border = thin_border
        c_val.border = thin_border

    # Hoja 2: Homologación (5 muestras)
    ws2 = wb.create_sheet(title="2. Homologación")
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
        # Hipervínculo
        link_url = m.get("link", "#")
        if not link_url.startswith("http"):
            link_url = "https://" + link_url
        link_cell = ws2.cell(row=f, column=3, value="Ver oferta")
        link_cell.hyperlink = link_url
        link_cell.font = Font(name="Arial", size=10, color="0563C1", underline="single")
        
        ws2.cell(row=f, column=4, value=m["precio_oferta"]).number_format = "#,##0"
        ws2.cell(row=f, column=5, value=m.get("fn", 0.95)).number_format = "0.00"
        ws2.cell(row=f, column=6, value=f"=D{f}*E{f}").number_format = "#,##0"
        area_val = m["area_construida"]  # siempre área construida para RPH
        ws2.cell(row=f, column=7, value=area_val).number_format = "#,##0.00"
        ws2.cell(row=f, column=8, value=f"=F{f}/G{f}").number_format = "#,##0"
        ws2.cell(row=f, column=9, value=m.get("f_ubicacion", 1.0)).number_format = "0.00"
        ws2.cell(row=f, column=10, value=m.get("f_edad", 1.0)).number_format = "0.00"
        ws2.cell(row=f, column=11, value=m.get("f_caracteristicas", 1.0)).number_format = "0.00"
        ws2.cell(row=f, column=12, value=f"=I{f}*J{f}*K{f}").number_format = "0.00"
        ws2.cell(row=f, column=13, value=f"=H{f}*L{f}").number_format = "#,##0"
        
        for col_c in range(1, 14):
            ws2.cell(row=f, column=col_c).border = thin_border
            if r_fill.fill_type: ws2.cell(row=f, column=col_c).fill = r_fill

    fila_fin = fila_inicio + len(muestras) - 1
    fila_prom = fila_fin + 2
    ws2.cell(row=fila_prom, column=1, value="PROMEDIO").font = font_bold
    ws2.cell(row=fila_prom, column=13, value=f"=AVERAGE(M{fila_inicio}:M{fila_fin})").font = font_bold
    ws2.cell(row=fila_prom, column=13).number_format = "#,##0"

    # Hoja 3: Análisis Estadístico
    ws3 = wb.create_sheet(title="3. Análisis Estadístico")
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

    ws3["D10"] = 1.15
    ws3["D10"].number_format = "0.000"
    ws3["D11"] = 0.85
    ws3["D11"].number_format = "0.000"

    ws3["A6"] = "Promedio del Valor M² Homogenizado"
    ws3["B6"] = f"='2. Homologación'!M{fila_prom}"
    ws3["B6"].number_format = "#,##0"; ws3["B6"].font = font_bold
    ws3["C6"] = "Base para la liquidación del metro cuadrado"
    
    ws3["A7"] = "Desviación Estándar de la Muestra (σ)"
    ws3["B7"] = f"=STDEV('2. Homologación'!M{fila_inicio}:M{fila_fin})"
    ws3["B7"].number_format = "#,##0"
    ws3["C7"] = "Mide el grado de dispersión de los precios de los portales"
    
    ws3["A8"] = "Coeficiente de Variación (CV)"
    ws3["B8"] = "=B7/B6"; ws3["B8"].number_format = "0.00%"; ws3["B8"].font = font_bold
    ws3["C8"] = "CRITERIO DE ALTA PRECISIÓN: Debe ser menor o igual al 15.00%"
    
    ws3["A9"] = "Coeficiente de Asimetría"
    ws3["B9"] = f"=SKEW('2. Homologación'!M{fila_inicio}:M{fila_fin})"
    ws3["B9"].number_format = "0.00"
    ws3["C9"] = "Mide la tendencia de sesgo de las ofertas"

    ws3["A10"] = "Límite Superior (15%)"
    ws3["B10"] = "=B6*D10"; ws3["B10"].number_format = "#,##0"
    ws3["A11"] = "Límite Inferior (15%)"
    ws3["B11"] = "=B6*D11"; ws3["B11"].number_format = "#,##0"

    ws3["A13"] = "LIQUIDACIÓN DEL VALOR COMERCIAL CONFORME A LA RESOLUCIÓN"
    ws3["A13"].font = font_bold
    ws3["A15"] = "Área del Inmueble Objetivo a Liquidar"
    ws3["B15"] = "='1. Ficha Inmueble Objetivo'!B12"   # Área Construida en la ficha
    ws3["B15"].number_format = "#,##0.00"
    ws3["C15"] = "Metros cuadrados tomados del informe físico"
    ws3["A16"] = "Valor por M² Homogenizado Adoptado"
    ws3["B16"] = "=B6"; ws3["B16"].number_format = "#,##0"; ws3["B16"].font = font_bold
    ws3["A17"] = "VALOR COMERCIAL TOTAL ESTIMADO"
    ws3["B17"] = "=B15*B16"; ws3["B17"].number_format = "$#,##0"
    ws3["B17"].font = Font(name="Arial", size=11, bold=True, color=navy_header)
    ws3["B17"].fill = fill_accent
    ws3["B17"].border = Border(bottom=Side(style='medium', color=navy_header))
    ws3["C17"] = "Resultado Final del Dictamen Técnico"

    for r in [6,7,8,9,10,11,15,16,17]:
        for col_c in range(1,4):
            ws3.cell(row=r, column=col_c).border = thin_border
    ws3.column_dimensions["D"].hidden = True

    for ws in [ws1, ws2, ws3]:
        for col in ws.columns:
            max_len = max((len(str(cell.value or '')) for cell in col), default=0)
            col_letter = get_column_letter(col[0].column)
            ws.column_dimensions[col_letter].width = min(max_len + 3, 30)

    buffer = io.BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    return buffer

def generar_excel_rph_no(datos_obj, muestras_completas, top5, calc_fitto):
    """Plantilla para casas (RPH=NO): Avalúo completo, Depurado, Fitto."""
    # Reutiliza la función anterior que ya tenías para no RPH (sin Links)
    # Por brevedad, aquí llamamos a la función que construye las 3 hojas de Diego.
    return fabricar_excel_diego(datos_obj, muestras_completas, top5, calc_fitto)

def fabricar_excel_diego(datos_obj, muestras_completas, top5, calc_fitto):
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

    # ---------- HOJA 1: AVALUO COMPLETO (8 muestras) ----------
    ws1 = wb.active
    ws1.title = "AVALUO CASA PRIMER PISO"
    _escribir_hoja_avaluo(ws1, datos_obj, muestras_completas, calc_fitto, 
                          font_title=font_title, font_header=font_header, font_bold=font_bold,
                          font_regular=font_regular, fill_header=fill_header, fill_zebra=fill_zebra,
                          fill_accent=fill_accent, thin_border=thin_border)

    # ---------- HOJA 2: AVALUO DEPURADO (5 mejores) ----------
    ws2 = wb.create_sheet(title="AVALUO DEPURADO")
    _escribir_hoja_avaluo(ws2, datos_obj, top5, calc_fitto,
                          font_title=font_title, font_header=font_header, font_bold=font_bold,
                          font_regular=font_regular, fill_header=fill_header, fill_zebra=fill_zebra,
                          fill_accent=fill_accent, thin_border=thin_border)

    # ---------- HOJA 3: FITTO CORVINI ----------
    ws3 = wb.create_sheet(title="FITTO CORVINI")
    _escribir_hoja_fitto(ws3, datos_obj, calc_fitto, font_title=font_title,
                         font_header=font_header, font_bold=font_bold, font_regular=font_regular,
                         fill_header=fill_header, thin_border=thin_border)

    for ws in [ws1, ws2, ws3]:
        for col in ws.columns:
            max_len = max((len(str(cell.value or '')) for cell in col), default=0)
            col_letter = get_column_letter(col[0].column)
            ws.column_dimensions[col_letter].width = min(max_len + 3, 30)

    buffer = io.BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    return buffer

# --- Funciones auxiliares para la plantilla Diego (no RPH) ---
def _escribir_hoja_avaluo(ws, datos, muestras, calc_fitto, **styles):
    ft = styles['font_title']; fh = styles['font_header']; fb = styles['font_bold']; fr = styles['font_regular']
    fh_fill = styles['fill_header']; bdr = styles['thin_border']

    ws["A2"] = "AVALUO CASA PRIMER PISO"
    ws["A2"].font = ft
    ws["A3"] = "No. Avalúo"
    ws["A4"] = "Direccion"
    ws["B4"] = f"{datos.get('barrio','')}, {datos.get('municipio','')}, Antioquia"
    ws["A5"] = "Area Const. M2"
    ws["B5"] = datos.get("area_construida", 0)
    ws["A6"] = "M.I."
    ws["B6"] = datos.get("matricula","")

    ws["A8"] = "HOMOGENIZADO APARTAMENTOS EN LA ZONA"
    ws["A8"].font = ft
    headers = ["Ítem", "Tipo de Inmueble", "Dirección y/o Ubicación", "Valor Pedido", "Area de Terreno",
               "Area Construida", "Valor Depreciado Construcción", "Valor Comercial del Terreno",
               "Valor M2 Depurado Terreno", "Eliminación Maximos - Minimos", "Link"]
    for c, h in enumerate(headers, 1):
        cell = ws.cell(row=9, column=c, value=h)
        cell.font = fh; cell.fill = fh_fill; cell.alignment = Alignment(horizontal="center")

    fila = 10
    for i, m in enumerate(muestras, 1):
        area_terreno_m = m.get("area_terreno", 0)
        area_construida_m = m.get("area_construida", 0)
        valor_depreciado_const = calc_fitto.get("valor_depreciado_m2", 0) * area_construida_m if area_construida_m > 0 else 0
        valor_comercial_terreno = m["precio_oferta"] - valor_depreciado_const
        valor_m2_depurado_terreno = valor_comercial_terreno / area_terreno_m if area_terreno_m > 0 else 0

        ws.cell(row=fila, column=1, value=i)
        ws.cell(row=fila, column=2, value="Lote de Terreno más Construcción")
        ws.cell(row=fila, column=3, value=f"{datos.get('municipio','')}")
        ws.cell(row=fila, column=4, value=m["precio_oferta"]).number_format = "#,##0"
        ws.cell(row=fila, column=5, value=area_terreno_m).number_format = "#,##0"
        ws.cell(row=fila, column=6, value=area_construida_m if area_construida_m > 0 else "N/A")
        ws.cell(row=fila, column=7, value=valor_depreciado_const).number_format = "#,##0"
        ws.cell(row=fila, column=8, value=valor_comercial_terreno).number_format = "#,##0"
        ws.cell(row=fila, column=9, value=valor_m2_depurado_terreno).number_format = "#,##0"
        ws.cell(row=fila, column=10, value=valor_m2_depurado_terreno)

        # Hipervínculo
        link_url = m.get("link", "#")
        if not link_url.startswith("http"):
            link_url = "https://" + link_url
        link_cell = ws.cell(row=fila, column=11, value="Ver oferta")
        link_cell.hyperlink = link_url
        link_cell.font = Font(name="Arial", size=10, color="0563C1", underline="single")

        for c in range(1, 12):
            ws.cell(row=fila, column=c).border = bdr
        fila += 1

    n_muestras = len(muestras)
    if n_muestras > 0:
        ws.cell(row=fila, column=9, value="Promedio").font = fb
        ws.cell(row=fila, column=10, value=f"=AVERAGE(J10:J{10+n_muestras-1})").number_format = "#,##0"
        fila += 1
        ws.cell(row=fila, column=9, value="Desviación Estándar").font = fb
        ws.cell(row=fila, column=10, value=f"=STDEV(J10:J{10+n_muestras-1})").number_format = "#,##0"
        fila += 1
        ws.cell(row=fila, column=9, value="Coeficiente Variación").font = fb
        ws.cell(row=fila, column=10, value=f"={fila-1}/{fila-2}").number_format = "0.00%"
        fila += 1
        ws.cell(row=fila, column=9, value="Coeficiente Asimetria").font = fb
        ws.cell(row=fila, column=10, value=f"=SKEW(J10:J{10+n_muestras-1})").number_format = "0.00"
        fila += 1
        ws.cell(row=fila, column=9, value="Límite Superior").font = fb
        ws.cell(row=fila, column=10, value=f"={fila-4}*1.15").number_format = "#,##0"
        fila += 1
        ws.cell(row=fila, column=9, value="Límite Inferior").font = fb
        ws.cell(row=fila, column=10, value=f"={fila-5}*0.85").number_format = "#,##0"
        fila += 1
        ws.cell(row=fila, column=9, value="VALOR ADOPTADO").font = fb
        ws.cell(row=fila, column=10, value=f"={fila-6}").number_format = "#,##0"
        fila_promedio = fila - 6

    # Liquidación
    fila += 2
    ws.cell(row=fila, column=1, value="IDENTIFICACIÓN DEL BIEN").font = fb
    ws.cell(row=fila, column=2, value="ÁREA"); ws.cell(row=fila, column=3, value="VALOR M2"); ws.cell(row=fila, column=4, value="VALOR TOTAL")
    fila += 1
    ws.cell(row=fila, column=1, value="LOTE DE TERRENO")
    ws.cell(row=fila, column=2, value=datos.get("area_terreno", 0))
    ws.cell(row=fila, column=3, value=f"={fila_promedio+4}")
    ws.cell(row=fila, column=4, value=f"=B{fila}*C{fila}").number_format = "#,##0"
    fila += 1
    ws.cell(row=fila, column=1, value="CONSTRUCCIÓN")
    ws.cell(row=fila, column=2, value=datos.get("area_construida", 0))
    ws.cell(row=fila, column=3, value=calc_fitto.get("valor_depreciado_m2", 0)).number_format = "#,##0"
    ws.cell(row=fila, column=4, value=f"=B{fila}*C{fila}").number_format = "#,##0"
    fila += 1
    ws.cell(row=fila, column=1, value="VALOR TOTAL DEL INMUEBLE").font = fb
    ws.cell(row=fila, column=4, value=f"=SUM(D{fila-2}:D{fila-1})").number_format = "#,##0"

def _escribir_hoja_fitto(ws, datos, calc, **styles):
    ft = styles['font_title']; fb = styles['font_bold']; fr = styles['font_regular']
    fh_fill = styles['fill_header']; bdr = styles['thin_border']
    ws["A2"] = "UNIFAMILIAR MEDIO - COSTO DE REPOSICIÓN"
    ws["A3"] = "Calculo Valor Depreciado (VIVIENDA DE USO HABITACIONAL - SUJETO)."
    ws["A4"] = "Método Fitto Corvini - Artículo 37 Numeral 9 - Depreciación (Resolución 620 de 2008)."
    headers = ["DESCRIPCIÓN", "VALOR", "UNIDAD / OBSERVACIÓN"]
    for c, h in enumerate(headers, 1):
        cell = ws.cell(row=6, column=c, value=h)
        cell.font = fb; cell.fill = fh_fill; cell.alignment = Alignment(horizontal="center")
    data = [
        ("Construcción aproximada", datos.get("area_construida", 0), "M2"),
        ("Edad", datos.get("edad_const", 0), "años aproximadamente"),
        ("Conservación", "", datos.get("conservacion", "")),
        ("Metodología (Depreciación acumulada)", "", "Fitto Corvini"),
        ("Costo directo de construcción actual por unidad", f"${datos.get('costo_reposicion_m2',0):,.0f}", "Pesos por M2"),
        ("Vida técnica", 70, "años"),
        ("Depreciación Calificación", 3.5, "Clase"),
        ("Coeficiente de depreciación", calc.get("coef", 0), ""),
        ("Valor a depreciar", f"${datos.get('costo_reposicion_m2',0) - calc.get('valor_depreciado_m2',0):,.0f}", "Pesos"),
        ("Valor depreciado de la construcción M2", f"${calc.get('valor_depreciado_m2',0):,.0f}", "Pesos"),
        ("Valor M2 de la construcción", f"${calc.get('valor_depreciado_m2',0):,.0f}", "Pesos por M2"),
        ("VALOR TOTAL CONSTRUCCIÓN", f"${calc.get('valor_total_construccion',0):,.0f}", "Pesos"),
    ]
    for r, (desc, val, unit) in enumerate(data, 7):
        ws.cell(row=r, column=1, value=desc)
        ws.cell(row=r, column=2, value=val)
        ws.cell(row=r, column=3, value=unit)
        for c in range(1, 4):
            ws.cell(row=r, column=c).border = bdr

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
        "area_terreno": area_terreno,
        "edad_const": edad_const,
        "conservacion": conservacion,
        "costo_reposicion_m2": costo_reposicion_m2
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
    
    if rph == "NO":
        calc_fitto = fitto_corvini(area_construida, edad_const, 70, conservacion, costo_reposicion_m2)
    else:
        calc_fitto = {}
    st.session_state.calc_fitto = calc_fitto
    
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
        
    if st.session_state.datos_inmueble["rph"] == "NO":
        excel_final = generar_excel_rph_no(st.session_state.datos_inmueble,
                                           st.session_state.muestras,
                                           st.session_state.top5_muestras,
                                           st.session_state.calc_fitto)
    else:
        excel_final = generar_excel_rph_si(st.session_state.datos_inmueble,
                                           st.session_state.top5_muestras)
    
    st.download_button(
        label="📥 Descargar Dictamen Técnico Oficial",
        data=excel_final,
        file_name=f"DICTAMEN_PRO_{st.session_state.datos_inmueble['barrio']}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True
    )
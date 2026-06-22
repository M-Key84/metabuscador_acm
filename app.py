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

# Inicialización de todas las variables de sesión
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
    st.session_state.calc_fitto = {}   # ← inicializado aquí

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

# --- Función para calcular Fitto Corvini ---
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

# --- Selección de las 5 mejores muestras ---
def seleccionar_top5_por_area(muestras, area_ref, es_rph):
    col_area = "area_construida" if es_rph == "SÍ" else "area_terreno"
    validas = [m for m in muestras if m.get(col_area, 0) > 0]
    if not validas:
        return muestras[:5]
    validas.sort(key=lambda x: abs(x[col_area] - area_ref))
    return validas[:5]

# --- Generación del Excel con 4 hojas ---
def fabricar_excel_completo(datos_obj, muestras_completas, top5, calc_fitto):
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
    _escribir_hoja_avaluo(ws1, datos_obj, muestras_completas, calc_fitto, es_completa=True, 
                          font_title=font_title, font_header=font_header, font_bold=font_bold,
                          font_regular=font_regular, fill_header=fill_header, fill_zebra=fill_zebra,
                          fill_accent=fill_accent, thin_border=thin_border)

    # ---------- HOJA 2: AVALUO DEPURADO (5 mejores) ----------
    ws2 = wb.create_sheet(title="AVALUO DEPURADO")
    _escribir_hoja_avaluo(ws2, datos_obj, top5, calc_fitto, es_completa=False,
                          font_title=font_title, font_header=font_header, font_bold=font_bold,
                          font_regular=font_regular, fill_header=fill_header, fill_zebra=fill_zebra,
                          fill_accent=fill_accent, thin_border=thin_border)

    # ---------- HOJA 3: FITTO CORVINI ----------
    ws3 = wb.create_sheet(title="FITTO CORVINI")
    _escribir_hoja_fitto(ws3, datos_obj, calc_fitto, font_title=font_title,
                         font_header=font_header, font_bold=font_bold, font_regular=font_regular,
                         fill_header=fill_header, thin_border=thin_border)

    # ---------- HOJA 4: LINKS ----------
    ws4 = wb.create_sheet(title="LINKS")
    _escribir_hoja_links(ws4, muestras_completas, font_title=font_title, font_bold=font_bold,
                         font_regular=font_regular, thin_border=thin_border)

    # Ajustar anchos de columna
    for ws in [ws1, ws2, ws3, ws4]:
        for col in ws.columns:
            max_len = max((len(str(cell.value or '')) for cell in col), default=0)
            col_letter = get_column_letter(col[0].column)
            ws.column_dimensions[col_letter].width = min(max_len + 3, 30)

    buffer = io.BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    return buffer

# --- Función auxiliar para escribir una hoja de avalúo ---
def _escribir_hoja_avaluo(ws, datos, muestras, calc_fitto, es_completa, **styles):
    ft = styles['font_title']; fh = styles['font_header']; fb = styles['font_bold']; fr = styles['font_regular']
    fh_fill = styles['fill_header']; fz = styles['fill_zebra']; fa = styles['fill_accent']
    bdr = styles['thin_border']

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
               "Valor M2 Depurado Terreno", "Eliminación Maximos - Minimos"]
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
        for c in range(1, 11):
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

# --- Hoja FITTO CORVINI ---
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

# --- Hoja LINKS ---
def _escribir_hoja_links(ws, muestras, **styles):
    ft = styles['font_title']; fb = styles['font_bold']; fr = styles['font_regular']; bdr = styles['thin_border']
    ws["A2"] = "MUESTRAS Y ENLACES DE VERIFICACIÓN"
    ws["A2"].font = ft
    ws.cell(row=4, column=1, value="Muestra").font = fb
    ws.cell(row=4, column=2, value="Portal").font = fb
    ws.cell(row=4, column=3, value="Link").font = fb
    for i, m in enumerate(muestras, 1):
        ws.cell(row=4+i, column=1, value=f"Muestra {i}")
        ws.cell(row=4+i, column=2, value=m.get("portal",""))
        ws.cell(row=4+i, column=3, value=m.get("link",""))
        for c in range(1, 4):
            ws.cell(row=4+i, column=c).border = bdr

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
    
    # Cálculo Fitto Corvini para el inmueble objetivo
    if rph == "NO":
        calc_fitto = fitto_corvini(area_construida, edad_const, 70, conservacion, costo_reposicion_m2)
    else:
        calc_fitto = {"coef": 0, "valor_depreciado_m2": 0, "valor_total_construccion": 0}
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
        
    excel_final = fabricar_excel_completo(st.session_state.datos_inmueble,
                                          st.session_state.muestras,
                                          st.session_state.top5_muestras,
                                          st.session_state.calc_fitto)
    
    st.download_button(
        label="📥 Descargar Dictamen Técnico Oficial (4 hojas: Avalúo, Depurado, Fitto, Links)",
        data=excel_final,
        file_name=f"DICTAMEN_PRO_{st.session_state.datos_inmueble['barrio']}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True
    )
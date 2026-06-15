import sqlite3
import requests
from datetime import datetime

DB_NAME = "mercado_inmobiliario.db"

def inicializar_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Tabla maestro de ofertas
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ofertas_portales (
            id_portal TEXT PRIMARY KEY,
            portal TEXT,
            municipio TEXT,
            barrio TEXT,
            precio_oferta REAL,
            area_construida REAL,
            area_terreno REAL,
            edad_construccion INTEGER,
            estado TEXT DEFAULT 'ACTIVO',
            fecha_creacion TEXT,
            ultima_vista TEXT
        )
    """)
    
    # Tabla de caché geográfica nacional (DANE)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS divipola_colombia (
            municipio TEXT,
            departamento TEXT,
            PRIMARY KEY(municipio, departamento)
        )
    """)
    conn.commit()
    conn.close()
    
    # Sembramos los municipios de toda Colombia de forma automática
    poblar_municipios_dane()

def poblar_municipios_dane():
    """Conexión al API de Datos Abiertos Colombia para devorar la estructura nacional"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM divipola_colombia")
    if cursor.fetchone()[0] > 0:
        conn.close()
        return # Ya está poblado, no gastamos ancho de banda
        
    try:
        # API oficial de municipios y departamentos de Colombia (Socrata API)
        url = "https://datos.gov.co/resource/xdk5-pm3f.json?$limit=5000"
        respuesta = requests.get(url, timeout=10)
        if respuesta.status_code == 200:
            datos = respuesta.json()
            for item in datos:
                mun = item.get("municipio", "").strip().title()
                dep = item.get("departamento", "").strip().title()
                if mun and dep:
                    cursor.execute("""
                        INSERT OR IGNORE INTO divipola_colombia (municipio, departamento)
                        VALUES (?, ?)
                    """, (mun, dep))
            conn.commit()
    except Exception:
        # Fallback de emergencia si el servidor de MinTIC está caído
        fallbacks = [("Medellín", "Antioquia"), ("Bello", "Antioquia"), ("Girardota", "Antioquia"), 
                     ("Bogotá", "Cundinamarca"), ("Cali", "Valle Del Cauca"), ("Barranquilla", "Atlántico")]
        cursor.executemany("INSERT OR IGNORE INTO divipola_colombia (municipio, departamento) VALUES (?,?)", fallbacks)
        conn.commit()
    finally:
        conn.close()

def obtener_municipios_totales():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT municipio FROM divipola_colombia ORDER BY municipio ASC")
    municipios = [fila[0] for fila in cursor.fetchall()]
    conn.close()
    return municipios

def guardar_muestras_upsert(muestras):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    fecha_hoy = datetime.now().strftime("%Y-%m-%d")
    
    for m in muestras:
        try:
            cursor.execute("""
                INSERT INTO ofertas_portales 
                (id_portal, portal, municipio, barrio, precio_oferta, area_construida, area_terreno, edad_construccion, fecha_creacion, ultima_vista)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                m["id_portal"], m["portal"], m["municipio"], m["barrio"],
                m["precio_oferta"], m["area_construida"], m["area_terreno"],
                m["edad_construccion"], fecha_hoy, fecha_hoy
            ))
        except sqlite3.IntegrityError:
            cursor.execute("""
                UPDATE ofertas_portales
                SET precio_oferta = ?, ultima_vista = ?, estado = 'ACTIVO'
                WHERE id_portal = ?
            """, (m["precio_oferta"], fecha_hoy, m["id_portal"]))
            
    conn.commit()
    conn.close()

def consultar_muestras_validas(municipio, barrio, area_obj, es_rph):
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    limite_inferior = area_obj * 0.7
    limite_superior = area_obj * 1.3
    columna_area = "area_construida" if es_rph == "SÍ" else "area_terreno"
    
    query = f"""
        SELECT * FROM ofertas_portales
        WHERE municipio = ? 
        AND barrio = ? 
        AND estado = 'ACTIVO'
        AND {columna_area} BETWEEN ? AND ?
        LIMIT 8
    """
    
    cursor.execute(query, (municipio, barrio, limite_inferior, limite_superior))
    filas = cursor.fetchall()
    conn.close()
    return [dict(f) for f in filas]
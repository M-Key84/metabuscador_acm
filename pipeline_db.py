import sqlite3
from datetime import datetime

DB_NAME = "mercado_inmobiliario.db"

def inicializar_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
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
    conn.commit()
    conn.close()

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
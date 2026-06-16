import sqlite3
from datetime import datetime

DB_NAME = "mercado_inmobiliario.db"

def inicializar_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Tabla de Ofertas con todos los campos de homologación requeridos por Diego
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
            fn REAL,
            f_ubicacion REAL,
            f_edad REAL,
            f_caracteristicas REAL,
            estado TEXT DEFAULT 'ACTIVO',
            fecha_creacion TEXT,
            ultima_vista TEXT
        )
    """)
    
    # Migración segura: añadir columnas de factores si no existen (para bases de datos antiguas)
    columnas_factores = [
        ("fn", "REAL"),
        ("f_ubicacion", "REAL"),
        ("f_edad", "REAL"),
        ("f_caracteristicas", "REAL")
    ]
    for nombre_col, tipo_col in columnas_factores:
        try:
            cursor.execute(f"ALTER TABLE ofertas_portales ADD COLUMN {nombre_col} {tipo_col}")
        except sqlite3.OperationalError:
            # La columna ya existe, ignorar error
            pass
    
    # Tabla Geográfica Maestra: Exclusiva Valle de Aburrá + Corregimientos
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS geografia_aburra (
            municipio TEXT,
            barrio_sector TEXT,
            PRIMARY KEY(municipio, barrio_sector)
        )
    """)
    conn.commit()
    conn.close()
    
    poblar_geografia_solicitada()

def poblar_geografia_solicitada():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM geografia_aburra")
    if cursor.fetchone()[0] > 0:
        conn.close()
        return
        
    catatogo_real = [
        ("Medellín", "El Poblado"), ("Medellín", "Laureles"), ("Medellín", "Belén"), 
        ("Medellín", "Conquistadores"), ("Medellín", "Guayabal"), ("Medellín", "Robledo"), 
        ("Medellín", "Aranjuez"), ("Medellín", "Buenos Aires"), ("Medellín", "La América"), 
        ("Medellín", "San Javier"), ("Medellín", "Centro"),
        ("Medellín", "Santa Elena (Corregimiento)"), 
        ("Medellín", "San Cristóbal (Corregimiento)"), 
        ("Medellín", "San Antonio de Prado (Corregimiento)"), 
        ("Medellín", "San Sebastián de Palmitas (Corregimiento)"), 
        ("Medellín", "Altavista (Corregimiento)"),
        ("Bello", "Cabañas"), ("Bello", "Niquía"), ("Bello", "Centro"), ("Bello", "Santa Ana"), ("Bello", "Bellavista"),
        ("Envigado", "Aves María"), ("Envigado", "Otraparte"), ("Envigado", "El Dorado"), ("Envigado", "La Sebastiana"), ("Envigado", "Zúñiga"),
        ("Sabaneta", "Centro"), ("Sabaneta", "La Doctora"), ("Sabaneta", "Pan de Azúcar"), ("Sabaneta", "Aliadas"),
        ("Itagüí", "Simón Bolívar"), ("Itagüí", "Centro"), ("Itagüí", "Santa María"), ("Itagüí", "Ditaires"),
        ("Copacabana", "Centro"), ("Copacabana", "Pedregal"), ("Copacabana", "Machado"),
        ("La Estrella", "Centro"), ("La Estrella", "La Tablaza"), ("La Estrella", "Suramérica"),
        ("Caldas", "Centro"), ("Caldas", "Andalucía"), ("Caldas", "La Valeria"),
        ("Girardota", "Centro"), ("Girardota", "El Llano"), ("Girardota", "Guayacanes"), ("Girardota", "San Esteban"),
        ("Barbosa", "Centro"), ("Barbosa", "El Hatillo")
    ]
    cursor.executemany("INSERT OR IGNORE INTO geografia_aburra (municipio, barrio_sector) VALUES (?, ?)", catatogo_real)
    conn.commit()
    conn.close()

def obtener_municipios_totales():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT municipio FROM geografia_aburra ORDER BY municipio ASC")
    municipios = [fila[0] for fila in cursor.fetchall()]
    conn.close()
    return municipios

def obtener_barrios_por_municipio(municipio):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT barrio_sector FROM geografia_aburra WHERE municipio = ? ORDER BY barrio_sector ASC", (municipio,))
    barrios = [fila[0] for fila in cursor.fetchall()]
    conn.close()
    return barrios

def guardar_muestras_upsert(muestras):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    fecha_hoy = datetime.now().strftime("%Y-%m-%d")
    
    REQUERIDAS = [
        "id_portal", "portal", "municipio", "barrio",
        "precio_oferta", "area_construida", "area_terreno", "edad_construccion"
    ]
    
    for i, m in enumerate(muestras):
        if not all(k in m for k in REQUERIDAS):
            continue   # omitir muestras incompletas
        
        try:
            cursor.execute("""
                INSERT INTO ofertas_portales 
                (id_portal, portal, municipio, barrio, precio_oferta, area_construida, area_terreno, edad_construccion, fn, f_ubicacion, f_edad, f_caracteristicas, fecha_creacion, ultima_vista)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                m["id_portal"], m["portal"], m["municipio"], m["barrio"],
                m["precio_oferta"], m["area_construida"], m["area_terreno"],
                m["edad_construccion"], m.get("fn", 0.95), m.get("f_ubicacion", 1.0), 
                m.get("f_edad", 1.0), m.get("f_caracteristicas", 1.0), fecha_hoy, fecha_hoy
            ))
        except sqlite3.IntegrityError:
            cursor.execute("""
                UPDATE ofertas_portales
                SET precio_oferta = ?, fn = ?, f_ubicacion = ?, f_edad = ?, f_caracteristicas = ?, ultima_vista = ?, estado = 'ACTIVO'
                WHERE id_portal = ?
            """, (m["precio_oferta"], m.get("fn", 0.95), m.get("f_ubicacion", 1.0), 
                  m.get("f_edad", 1.0), m.get("f_caracteristicas", 1.0), fecha_hoy, m["id_portal"]))
            
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
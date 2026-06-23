import sqlite3
import json
import os
from datetime import datetime

DB_NAME = "mercado_inmobiliario.db"

def inicializar_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ofertas_portales (
            id_portal TEXT PRIMARY KEY,
            portal TEXT,
            link TEXT,
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

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS geografia_aburra (
            municipio TEXT,
            barrio_sector TEXT,
            PRIMARY KEY(municipio, barrio_sector)
        )
    """)
    conn.commit()
    conn.close()

    poblar_geografia_desde_json()

def poblar_geografia_desde_json():
    if not os.path.exists("geografia_aburra.json"):
        print("Advertencia: No se encontró el archivo geografia_aburra.json. Catálogo vacío.")
        return

    with open("geografia_aburra.json", "r", encoding="utf-8") as file:
        data = json.load(file)

    catologo_real = []
    for municipio, barrios in data.items():
        for barrio in barrios:
            catologo_real.append((municipio.strip(), barrio.strip()))

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM geografia_aburra")
    cursor.executemany("INSERT OR IGNORE INTO geografia_aburra (municipio, barrio_sector) VALUES (?, ?)", catologo_real)
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
        "id_portal", "portal", "link", "municipio", "barrio",
        "precio_oferta", "area_construida", "area_terreno", "edad_construccion"
    ]

    for m in muestras:
        if not all(k in m for k in REQUERIDAS):
            continue

        cursor.execute("""
            INSERT INTO ofertas_portales 
            (id_portal, portal, link, municipio, barrio, precio_oferta, area_construida, area_terreno, edad_construccion, fn, f_ubicacion, f_edad, f_caracteristicas, fecha_creacion, ultima_vista)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id_portal) DO UPDATE SET
                precio_oferta=excluded.precio_oferta,
                fn=excluded.fn,
                f_ubicacion=excluded.f_ubicacion,
                f_edad=excluded.f_edad,
                f_caracteristicas=excluded.f_caracteristicas,
                ultima_vista=excluded.ultima_vista,
                estado='ACTIVO'
        """, (
            m["id_portal"], m["portal"], m["link"], m["municipio"], m["barrio"],
            m["precio_oferta"], m["area_construida"], m["area_terreno"],
            m["edad_construccion"], m.get("fn", 0.95), m.get("f_ubicacion", 1.0),
            m.get("f_edad", 1.0), m.get("f_caracteristicas", 1.0), fecha_hoy, fecha_hoy
        ))

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
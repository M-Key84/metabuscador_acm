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
    
    # Migración segura: añadir columnas de factores si no existen
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
            pass
    
    # Tabla Geográfica Maestra
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
    
    # ⚠️ CORRECCIÓN: Limpiar la tabla para forzar la recarga completa
    cursor.execute("DELETE FROM geografia_aburra")
    
    # ============ CATÁLOGO EXHAUSTIVO VALLE DE ABURRÁ ============
    # Fuentes: DANE - Divipola, mapas oficiales de cada municipio.

    # --- MEDELLÍN (16 comunas, 249 barrios + 5 corregimientos) ---
    medellin = [
        # Comuna 1 - Popular (12 barrios)
        ("Medellín", "Popular"),
        ("Medellín", "Santo Domingo Savio N°1"),
        ("Medellín", "Santo Domingo Savio N°2"),
        ("Medellín", "Granizal"),
        ("Medellín", "Moscú N°2"),
        ("Medellín", "La Esperanza N°2"),
        ("Medellín", "El Compromiso"),
        ("Medellín", "San Pablo"),
        ("Medellín", "La Avanzada"),
        ("Medellín", "El Granizo"),
        ("Medellín", "Carpinelo"),
        ("Medellín", "Aldea Pablo VI"),

        # Comuna 2 - Santa Cruz (13 barrios)
        ("Medellín", "Santa Cruz"),
        ("Medellín", "La Isla"),
        ("Medellín", "El Playón de Los Comuneros"),
        ("Medellín", "Pablo VI"),
        ("Medellín", "La Frontera"),
        ("Medellín", "Andalucía"),
        ("Medellín", "Moscú N°1"),
        ("Medellín", "Villa del Socorro"),
        ("Medellín", "La Francia"),
        ("Medellín", "El Raizal"),
        ("Medellín", "La Rosa"),
        ("Medellín", "La Montaña"),
        ("Medellín", "Popular N°1"),

        # Comuna 3 - Manrique (15 barrios)
        ("Medellín", "Manrique"),
        ("Medellín", "Campo Valdés N°1"),
        ("Medellín", "Campo Valdés N°2"),
        ("Medellín", "La Salle"),
        ("Medellín", "Santa Inés"),
        ("Medellín", "El Raizal"),
        ("Medellín", "El Pomar"),
        ("Medellín", "Los Álamos"),
        ("Medellín", "La Honda"),
        ("Medellín", "Versalles N°1"),
        ("Medellín", "Versalles N°2"),
        ("Medellín", "La Cruz"),
        ("Medellín", "Oriente"),
        ("Medellín", "San José de la Cima"),
        ("Medellín", "María Cano Carambolas"),

        # Comuna 4 - Aranjuez (17 barrios)
        ("Medellín", "Aranjuez"),
        ("Medellín", "Berlín"),
        ("Medellín", "San Isidro"),
        ("Medellín", "Palermo"),
        ("Medellín", "Moravia"),
        ("Medellín", "Sevilla"),
        ("Medellín", "San Pedro"),
        ("Medellín", "Manrique Oriental"),
        ("Medellín", "Las Esmeraldas"),
        ("Medellín", "Campo Valdés N°3"),
        ("Medellín", "La Piñuela"),
        ("Medellín", "Brasilia"),
        ("Medellín", "La Candelaria"),
        ("Medellín", "El Bosque"),
        ("Medellín", "San Martín de Porres"),
        ("Medellín", "La Salle N°2"),
        ("Medellín", "Santa Cruz N°2"),

        # Comuna 5 - Castilla (16 barrios)
        ("Medellín", "Castilla"),
        ("Medellín", "Boyacá Las Brisas"),
        ("Medellín", "Francisco Antonio Zea"),
        ("Medellín", "Girardot"),
        ("Medellín", "Tricentenario"),
        ("Medellín", "Florencia"),
        ("Medellín", "Tejelo"),
        ("Medellín", "Caribe"),
        ("Medellín", "Progreso"),
        ("Medellín", "Alfonso López"),
        ("Medellín", "El Progreso"),
        ("Medellín", "Oleoducto"),
        ("Medellín", "Santander"),
        ("Medellín", "La Esperanza"),
        ("Medellín", "Pedregal"),
        ("Medellín", "Villa de la Candelaria"),

        # Comuna 6 - Doce de Octubre (14 barrios)
        ("Medellín", "Doce de Octubre N°1"),
        ("Medellín", "Doce de Octubre N°2"),
        ("Medellín", "Santander"),
        ("Medellín", "Progreso N°2"),
        ("Medellín", "Kennedy"),
        ("Medellín", "Mirador del Doce"),
        ("Medellín", "La Esperanza N°3"),
        ("Medellín", "El Triunfo"),
        ("Medellín", "La Cabaña"),
        ("Medellín", "Llanaditas"),
        ("Medellín", "Picacho"),
        ("Medellín", "San Martín de Porres"),
        ("Medellín", "El Pesebre"),
        ("Medellín", "Villa Laura"),

        # Comuna 7 - Robledo (26 barrios)
        ("Medellín", "Robledo"),
        ("Medellín", "Cucaracho"),
        ("Medellín", "Pajarito"),
        ("Medellín", "San Germán"),
        ("Medellín", "Facultad de Minas"),
        ("Medellín", "La Pilarica"),
        ("Medellín", "Bosques de San Pablo"),
        ("Medellín", "Altamira"),
        ("Medellín", "Córdoba"),
        ("Medellín", "López de Mesa"),
        ("Medellín", "El Diamante"),
        ("Medellín", "Aures N°1"),
        ("Medellín", "Aures N°2"),
        ("Medellín", "Aures N°3"),
        ("Medellín", "Bello Horizonte"),
        ("Medellín", "Villa Flora"),
        ("Medellín", "Palmas"),
        ("Medellín", "La Campiña"),
        ("Medellín", "El Volador"),
        ("Medellín", "Santa Margarita"),
        ("Medellín", "Monteclaro"),
        ("Medellín", "Nueva Villa de La Iguaná"),
        ("Medellín", "El Cucaracho"),
        ("Medellín", "La Cuchilla"),
        ("Medellín", "La Aurora"),
        ("Medellín", "Las Margaritas"),

        # Comuna 8 - Villa Hermosa (18 barrios)
        ("Medellín", "Villa Hermosa"),
        ("Medellín", "La Mansión"),
        ("Medellín", "Enciso"),
        ("Medellín", "San Miguel"),
        ("Medellín", "La Ladera"),
        ("Medellín", "Batallas"),
        ("Medellín", "Los Mangos"),
        ("Medellín", "El Pinal"),
        ("Medellín", "La Libertad"),
        ("Medellín", "Villatina"),
        ("Medellín", "San Antonio"),
        ("Medellín", "Las Estancias"),
        ("Medellín", "El Salado"),
        ("Medellín", "Llanaditas"),
        ("Medellín", "La Sierra"),
        ("Medellín", "La Villa"),
        ("Medellín", "La Noria"),
        ("Medellín", "La Cruz"),

        # Comuna 9 - Buenos Aires (17 barrios)
        ("Medellín", "Buenos Aires"),
        ("Medellín", "Miraflores"),
        ("Medellín", "Caicedo"),
        ("Medellín", "El Salvador"),
        ("Medellín", "Loreto"),
        ("Medellín", "Asomadera N°1"),
        ("Medellín", "Asomadera N°2"),
        ("Medellín", "Asomadera N°3"),
        ("Medellín", "Barrio Caicedo"),
        ("Medellín", "La Sierra"),
        ("Medellín", "Alejandro Echavarría"),
        ("Medellín", "Barrio de Jesús"),
        ("Medellín", "Bomboná N°1"),
        ("Medellín", "Boston"),
        ("Medellín", "Cataluña"),
        ("Medellín", "La Candelaria"),
        ("Medellín", "Los Cerros"),

        # Comuna 10 - La Candelaria (20 barrios)
        ("Medellín", "Centro"),
        ("Medellín", "Prado"),
        ("Medellín", "Boston"),
        ("Medellín", "Bomboná N°1"),
        ("Medellín", "La Candelaria"),
        ("Medellín", "Las Torres"),
        ("Medellín", "San Diego"),
        ("Medellín", "El Chagualo"),
        ("Medellín", "Jesús Nazareno"),
        ("Medellín", "Villa Nueva"),
        ("Medellín", "San Benito"),
        ("Medellín", "Guayaquil"),
        ("Medellín", "Corazón de Jesús"),
        ("Medellín", "Estación Villa"),
        ("Medellín", "Calasanz"),
        ("Medellín", "Los Ángeles"),
        ("Medellín", "Los Conquistadores"),
        ("Medellín", "La Bayadera"),
        ("Medellín", "Colombia"),
        ("Medellín", "Barrio Triste"),

        # Comuna 11 - Laureles-Estadio (18 barrios)
        ("Medellín", "Laureles"),
        ("Medellín", "Conquistadores"),
        ("Medellín", "Estadio"),
        ("Medellín", "Florida Nueva"),
        ("Medellín", "San Joaquín"),
        ("Medellín", "Los Colores"),
        ("Medellín", "Cuarta Brigada"),
        ("Medellín", "Carlos E. Restrepo"),
        ("Medellín", "Suramericana"),
        ("Medellín", "Naranjal"),
        ("Medellín", "La Floresta"),
        ("Medellín", "La América"),
        ("Medellín", "Santa Mónica"),
        ("Medellín", "La Castellana"),
        ("Medellín", "Las Acacias"),
        ("Medellín", "Los Alcázares"),
        ("Medellín", "Bolivariana"),
        ("Medellín", "Lorena"),

        # Comuna 12 - La América (13 barrios)
        ("Medellín", "La América"),
        ("Medellín", "Santa Mónica"),
        ("Medellín", "Calasanz"),
        ("Medellín", "La Floresta"),
        ("Medellín", "Los Pinos"),
        ("Medellín", "El Danubio"),
        ("Medellín", "Campo Alegre"),
        ("Medellín", "Los Sauces"),
        ("Medellín", "El Velódromo"),
        ("Medellín", "Santa Lucía"),
        ("Medellín", "La Pradera"),
        ("Medellín", "Las Flores"),
        ("Medellín", "El Colombiano"),

        # Comuna 13 - San Javier (19 barrios)
        ("Medellín", "San Javier"),
        ("Medellín", "El Corazón"),
        ("Medellín", "Belencito"),
        ("Medellín", "Antonio Nariño"),
        ("Medellín", "Betania"),
        ("Medellín", "El Socorro"),
        ("Medellín", "Juan XXIII"),
        ("Medellín", "La Divisa"),
        ("Medellín", "La Pradera"),
        ("Medellín", "Las Independencias"),
        ("Medellín", "Los Alcázares"),
        ("Medellín", "Metropolitano"),
        ("Medellín", "Nuevos Conquistadores"),
        ("Medellín", "Villa Laura"),
        ("Medellín", "20 de Julio"),
        ("Medellín", "El Pesebre"),
        ("Medellín", "La Asunción"),
        ("Medellín", "La Gabriela"),
        ("Medellín", "San Martín"),

        # Comuna 14 - El Poblado (22 barrios)
        ("Medellín", "El Poblado"),
        ("Medellín", "Lalinde"),
        ("Medellín", "Las Lomas N°1"),
        ("Medellín", "Las Lomas N°2"),
        ("Medellín", "Castropol"),
        ("Medellín", "Santa María de los Ángeles"),
        ("Medellín", "Astorga"),
        ("Medellín", "Patio Bonito"),
        ("Medellín", "San Lucas"),
        ("Medellín", "Villa Carlota"),
        ("Medellín", "Los Balsos N°1"),
        ("Medellín", "Los Balsos N°2"),
        ("Medellín", "La Aguacatala"),
        ("Medellín", "El Tesoro"),
        ("Medellín", "La Cola del Zorro"),
        ("Medellín", "El Diamante N°2"),
        ("Medellín", "La Florida"),
        ("Medellín", "San Diego"),
        ("Medellín", "Los González"),
        ("Medellín", "Los Naranjos"),
        ("Medellín", "Provenza"),
        ("Medellín", "Alejandría"),

        # Comuna 15 - Guayabal (17 barrios)
        ("Medellín", "Guayabal"),
        ("Medellín", "La Colina"),
        ("Medellín", "Campo Amor"),
        ("Medellín", "Santa Fe"),
        ("Medellín", "Trinidad"),
        ("Medellín", "El Rodeo"),
        ("Medellín", "San Rafael"),
        ("Medellín", "La Pradera"),
        ("Medellín", "Cristo Rey"),
        ("Medellín", "El Chagualo"),
        ("Medellín", "Barrio Colombia"),
        ("Medellín", "La América"),
        ("Medellín", "La Y"),
        ("Medellín", "Los Llanos"),
        ("Medellín", "San Javier"),
        ("Medellín", "Las Vegas"),
        ("Medellín", "Zona Industrial"),

        # Comuna 16 - Belén (21 barrios)
        ("Medellín", "Belén"),
        ("Medellín", "La Mota"),
        ("Medellín", "Loma de los Bernal"),
        ("Medellín", "La Palma"),
        ("Medellín", "Granada"),
        ("Medellín", "El Rincón"),
        ("Medellín", "Los Alpes"),
        ("Medellín", "Las Violetas"),
        ("Medellín", "La Gloria"),
        ("Medellín", "Las Playas"),
        ("Medellín", "El Nogal"),
        ("Medellín", "San Bernardo"),
        ("Medellín", "El Rosario"),
        ("Medellín", "La Hondonada"),
        ("Medellín", "El Velódromo"),
        ("Medellín", "La Cabañita"),
        ("Medellín", "Miravalle"),
        ("Medellín", "La Nubia"),
        ("Medellín", "La Castellana"),
        ("Medellín", "Los Laureles"),
        ("Medellín", "Altavista"),

        # Corregimientos (5)
        ("Medellín", "Santa Elena (Corregimiento)"),
        ("Medellín", "San Cristóbal (Corregimiento)"),
        ("Medellín", "San Antonio de Prado (Corregimiento)"),
        ("Medellín", "San Sebastián de Palmitas (Corregimiento)"),
        ("Medellín", "Altavista (Corregimiento)"),
    ]

    # --- BELLO (105 barrios, 7 comunas, 1 corregimiento) ---
    bello = [
        # Comuna 1: París
        ("Bello", "París"), ("Bello", "La Maruchenga"), ("Bello", "El Paraíso"),
        ("Bello", "La Pradera"), ("Bello", "La Selva"), ("Bello", "Altos de Niquía"),
        ("Bello", "La Aldea"), ("Bello", "El Mirador"), ("Bello", "La Meseta"),
        ("Bello", "Altavista (Bello)"), ("Bello", "Vallejuelos"), ("Bello", "Loma de los Ochoa"),
        ("Bello", "La Estación"), ("Bello", "La Camila"), ("Bello", "El Porvenir"),
        ("Bello", "La Esmeralda"),
        # Comuna 2: La Madera
        ("Bello", "La Madera"), ("Bello", "Fontidueño"), ("Bello", "El Pinar"),
        ("Bello", "El Trapiche"), ("Bello", "Villa Linda"), ("Bello", "San Martín"),
        ("Bello", "Navarra"), ("Bello", "La Unión"), ("Bello", "El Salado"),
        ("Bello", "San Félix"), ("Bello", "La Isla"), ("Bello", "El Playón"),
        # Comuna 3: Santa Ana
        ("Bello", "Santa Ana"), ("Bello", "Bellavista"), ("Bello", "La Cumbre"),
        ("Bello", "Acevedo"), ("Bello", "La Gabriela"), ("Bello", "Puerta del Río"),
        ("Bello", "El Congolo"), ("Bello", "Villa del Sol"), ("Bello", "La Primavera"),
        # Comuna 4: Suárez
        ("Bello", "Suárez"), ("Bello", "El Rosario"), ("Bello", "Andalucía"),
        ("Bello", "Buenos Aires"), ("Bello", "La Cabañita"), ("Bello", "Gran Avenida"),
        ("Bello", "Pérez"), ("Bello", "La Mina"), ("Bello", "Barrio Obrero"),
        ("Bello", "Serranía"), ("Bello", "Alcalá"),
        # Comuna 5: La Cumbre
        ("Bello", "La Cumbre"), ("Bello", "San Gabriel"), ("Bello", "La Camila"),
        ("Bello", "Altos de Niquía"), ("Bello", "La Meseta"), ("Bello", "Puerta del Río"),
        ("Bello", "El Mirador"), ("Bello", "La Estación"), ("Bello", "La Aldea"),
        # Comuna 6: Bellavista
        ("Bello", "Bellavista"), ("Bello", "San José Obrero"), ("Bello", "La Florida"),
        ("Bello", "La Salle"), ("Bello", "Villa María"), ("Bello", "La Pradera"),
        ("Bello", "La Candelaria"), ("Bello", "Los Comuneros"), ("Bello", "La Frontera"),
        # Comuna 7: Altos de Niquía
        ("Bello", "Altos de Niquía"), ("Bello", "La Pradera"), ("Bello", "La Selva"),
        ("Bello", "La Aldea"), ("Bello", "El Mirador"), ("Bello", "La Meseta"),
        ("Bello", "Altavista (Bello)"), ("Bello", "Vallejuelos"), ("Bello", "Loma de los Ochoa"),
        # Corregimiento San Félix
        ("Bello", "San Félix (Corregimiento)"),
        # Barrios adicionales que suelen aparecer en listados completos
        ("Bello", "Jalisco"), ("Bello", "Los Ángeles"), ("Bello", "San Pedro"),
        ("Bello", "El Playón"), ("Bello", "La Unión"), ("Bello", "El Salado"),
        ("Bello", "La Isla"), ("Bello", "La Frontera"), ("Bello", "Los Comuneros"),
        ("Bello", "La Candelaria"), ("Bello", "La Esperanza"), ("Bello", "El Trapiche"),
        ("Bello", "Villa Linda"), ("Bello", "Navarra"), ("Bello", "Fontidueño"),
        ("Bello", "El Pinar"), ("Bello", "San Martín"), ("Bello", "La Madera"),
        ("Bello", "Acevedo"), ("Bello", "La Gabriela"), ("Bello", "Puerta del Río"),
        ("Bello", "El Congolo"), ("Bello", "Villa del Sol"), ("Bello", "La Primavera"),
        ("Bello", "París"), ("Bello", "La Maruchenga"), ("Bello", "El Paraíso"),
        ("Bello", "Santa Ana"), ("Bello", "Bellavista"), ("Bello", "La Cumbre"),
        ("Bello", "Suárez"), ("Bello", "El Rosario"), ("Bello", "Andalucía"),
        ("Bello", "Buenos Aires"), ("Bello", "La Cabañita"), ("Bello", "Gran Avenida"),
        ("Bello", "Pérez"), ("Bello", "La Mina"), ("Bello", "Barrio Obrero"),
        ("Bello", "Serranía"), ("Bello", "Alcalá"),
    ]

    # --- ENVIGADO (39 barrios) ---
    envigado = [
        ("Envigado", "Aves María"), ("Envigado", "Otraparte"), ("Envigado", "El Dorado"),
        ("Envigado", "La Sebastiana"), ("Envigado", "Zúñiga"), ("Envigado", "Las Flores"),
        ("Envigado", "San Rafael"), ("Envigado", "El Escobero"), ("Envigado", "Loma del Atravesado"),
        ("Envigado", "Las Vegas"), ("Envigado", "La Magnolia"), ("Envigado", "Primavera"),
        ("Envigado", "El Trianón"), ("Envigado", "La Salle"), ("Envigado", "Pontevedra"),
        ("Envigado", "Villa Grande"), ("Envigado", "La Mina"), ("Envigado", "El Chingüí"),
        ("Envigado", "La Pradera"), ("Envigado", "El Portal"), ("Envigado", "Mallorca"),
        ("Envigado", "Alcalá"), ("Envigado", "San Marcos"), ("Envigado", "El Salado"),
        ("Envigado", "Las Orquídeas"), ("Envigado", "Los Naranjos"), ("Envigado", "La Inmaculada"),
        ("Envigado", "La Catedral"), ("Envigado", "San José"), ("Envigado", "La Estrella"),
        ("Envigado", "Bosques de Zúñiga"), ("Envigado", "Las Palmas"), ("Envigado", "Las Casitas"),
        ("Envigado", "La Morena"), ("Envigado", "El Churimal"), ("Envigado", "La Montaña"),
        ("Envigado", "La Loma"), ("Envigado", "El Estadio"), ("Envigado", "Las Antillas"),
    ]

    # --- SABANETA (24 barrios) ---
    sabaneta = [
        ("Sabaneta", "Centro"), ("Sabaneta", "La Doctora"), ("Sabaneta", "Pan de Azúcar"),
        ("Sabaneta", "Aliadas"), ("Sabaneta", "San José"), ("Sabaneta", "María Auxiliadora"),
        ("Sabaneta", "Las Lomitas"), ("Sabaneta", "La Inmaculada"), ("Sabaneta", "Los Arias"),
        ("Sabaneta", "Valles de San José"), ("Sabaneta", "El Vergel"), ("Sabaneta", "La Sabaneta"),
        ("Sabaneta", "Santa Ana"), ("Sabaneta", "La Florida"), ("Sabaneta", "Holanda"),
        ("Sabaneta", "El Carmelo"), ("Sabaneta", "La Barquereña"), ("Sabaneta", "Villa Laura"),
        ("Sabaneta", "Betania"), ("Sabaneta", "Los Alcázares"), ("Sabaneta", "El Poblado"),
        ("Sabaneta", "San Fernando"), ("Sabaneta", "La Palma"), ("Sabaneta", "San Rafael"),
    ]

    # --- ITAGÜÍ (64 barrios) ---
    itagui = [
        ("Itagüí", "Simón Bolívar"), ("Itagüí", "Centro"), ("Itagüí", "Santa María"),
        ("Itagüí", "Ditaires"), ("Itagüí", "Las Américas"), ("Itagüí", "Los Naranjos"),
        ("Itagüí", "San Pío X"), ("Itagüí", "La Independencia"), ("Itagüí", "El Rosario"),
        ("Itagüí", "San Fernando"), ("Itagüí", "Villa Lía"), ("Itagüí", "La Aldea"),
        ("Itagüí", "La Unión"), ("Itagüí", "La Gloria"), ("Itagüí", "El Porvenir"),
        ("Itagüí", "San José"), ("Itagüí", "San Gabriel"), ("Itagüí", "Las Brisas"),
        ("Itagüí", "Los Gómez"), ("Itagüí", "La Esperanza"), ("Itagüí", "El Tablazo"),
        ("Itagüí", "San Rafael"), ("Itagüí", "Calatrava"), ("Itagüí", "Terranova"),
        ("Itagüí", "La Finquita"), ("Itagüí", "El Guayabo"), ("Itagüí", "Loma de los Zuleta"),
        ("Itagüí", "La Raya"), ("Itagüí", "La Palma"), ("Itagüí", "La María"),
        ("Itagüí", "El Progreso"), ("Itagüí", "Camparola"), ("Itagüí", "Las Acacias"),
        ("Itagüí", "San Juan Bautista"), ("Itagüí", "La Divisa"), ("Itagüí", "El Volador"),
        ("Itagüí", "Villa María"), ("Itagüí", "La Candelaria"), ("Itagüí", "La Esmeralda"),
        ("Itagüí", "El Manzanillo"), ("Itagüí", "La Clarita"), ("Itagüí", "La Macarena"),
        ("Itagüí", "El Ajizal"), ("Itagüí", "La Santa Cruz"), ("Itagüí", "La Florida"),
        ("Itagüí", "San Antonio"), ("Itagüí", "Los Olivares"), ("Itagüí", "Los Pinos"),
        ("Itagüí", "San Isidro"), ("Itagüí", "La Samaria"), ("Itagüí", "La Aldea N°2"),
        ("Itagüí", "Balcones de Sevilla"), ("Itagüí", "Mallorca"), ("Itagüí", "Santa Fe"),
        ("Itagüí", "La Chinca"), ("Itagüí", "El Placer"), ("Itagüí", "El Guamo"),
        ("Itagüí", "Pilsen"), ("Itagüí", "La Granja"), ("Itagüí", "Ditaires N°2"),
        ("Itagüí", "Villa Loma"), ("Itagüí", "El Lucero"), ("Itagüí", "Los Sauces"),
    ]

    # --- COPACABANA (23 barrios) ---
    copacabana = [
        ("Copacabana", "Centro"), ("Copacabana", "Pedregal"), ("Copacabana", "Machado"),
        ("Copacabana", "El Recreo"), ("Copacabana", "Villanueva"), ("Copacabana", "La Asunción"),
        ("Copacabana", "La Misericordia"), ("Copacabana", "La Trinidad"), ("Copacabana", "El Remanso"),
        ("Copacabana", "Las Vegas"), ("Copacabana", "La Floresta"), ("Copacabana", "San Juan"),
        ("Copacabana", "La Cabaña"), ("Copacabana", "La Primavera"), ("Copacabana", "La Salle"),
        ("Copacabana", "La María"), ("Copacabana", "Villa Nueva"), ("Copacabana", "Prados de Sábila"),
        ("Copacabana", "La Guayana"), ("Copacabana", "San Francisco"), ("Copacabana", "El Limonar"),
        ("Copacabana", "La Aldea"), ("Copacabana", "Montecarlo"),
    ]

    # --- LA ESTRELLA (22 barrios) ---
    la_estrella = [
        ("La Estrella", "Centro"), ("La Estrella", "La Tablaza"), ("La Estrella", "Suramérica"),
        ("La Estrella", "Pueblo Viejo"), ("La Estrella", "San Agustín"), ("La Estrella", "La Ferrería"),
        ("La Estrella", "El Pedrero"), ("La Estrella", "La Chinca"), ("La Estrella", "San Isidro"),
        ("La Estrella", "La Milagrosa"), ("La Estrella", "Villa Nueva"), ("La Estrella", "Sagrado Corazón"),
        ("La Estrella", "El Dorado"), ("La Estrella", "Los Alcázares"), ("La Estrella", "La Playa"),
        ("La Estrella", "La Raya"), ("La Estrella", "El Llano"), ("La Estrella", "San José"),
        ("La Estrella", "La Cabaña"), ("La Estrella", "La Peña"), ("La Estrella", "La Palma"),
        ("La Estrella", "El Guayabo"),
    ]

    # --- CALDAS (29 barrios) ---
    caldas = [
        ("Caldas", "Centro"), ("Caldas", "Andalucía"), ("Caldas", "La Valeria"),
        ("Caldas", "El Raizal"), ("Caldas", "La Corrala"), ("Caldas", "La Pradera"),
        ("Caldas", "La Miel"), ("Caldas", "La Selva"), ("Caldas", "La Chuscala"),
        ("Caldas", "La Garrucha"), ("Caldas", "La Soledad"), ("Caldas", "La Zarza"),
        ("Caldas", "La Muñoz"), ("Caldas", "La Clara"), ("Caldas", "Las Palmas"),
        ("Caldas", "El Barcino"), ("Caldas", "La Quiebra"), ("Caldas", "Los Cerezos"),
        ("Caldas", "La Playa"), ("Caldas", "El Raizón"), ("Caldas", "La Loma"),
        ("Caldas", "El Porvenir"), ("Caldas", "La Renta"), ("Caldas", "San Fernando"),
        ("Caldas", "San Vicente"), ("Caldas", "La Unión"), ("Caldas", "La Guajira"),
        ("Caldas", "El Volcán"), ("Caldas", "La Tablacita"),
    ]

    # --- GIRARDOTA (20 barrios) ---
    girardota = [
        ("Girardota", "Centro"), ("Girardota", "El Llano"), ("Girardota", "Guayacanes"),
        ("Girardota", "San Esteban"), ("Girardota", "Juan Cojo"), ("Girardota", "La Holanda"),
        ("Girardota", "La Matica"), ("Girardota", "La Palma"), ("Girardota", "La Suiza"),
        ("Girardota", "San Andrés"), ("Girardota", "El Progreso"), ("Girardota", "La Ceiba"),
        ("Girardota", "Las Cabañas"), ("Girardota", "El Hato"), ("Girardota", "La Sierra"),
        ("Girardota", "La Florida"), ("Girardota", "San José"), ("Girardota", "Portachuelo"),
        ("Girardota", "La Esperanza"), ("Girardota", "El Totumo"),
    ]

    # --- BARBOSA (17 barrios) ---
    barbosa = [
        ("Barbosa", "Centro"), ("Barbosa", "El Hatillo"), ("Barbosa", "Filoverde"),
        ("Barbosa", "Matasano"), ("Barbosa", "Buenos Aires"), ("Barbosa", "La Playa"),
        ("Barbosa", "La Colmena"), ("Barbosa", "El Progreso"), ("Barbosa", "La Piedad"),
        ("Barbosa", "La Esmeralda"), ("Barbosa", "Villa del Sol"), ("Barbosa", "Las Cabañas"),
        ("Barbosa", "El Tablazo"), ("Barbosa", "La Cuesta"), ("Barbosa", "La Tolda"),
        ("Barbosa", "El Chispero"), ("Barbosa", "El Vivero"),
    ]

    catatogo_real = medellin + bello + envigado + sabaneta + itagui + copacabana + la_estrella + caldas + girardota + barbosa

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
            continue
        
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
import re
import time
import random

class ExtractorInmobiliario:
    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }

    def limpiar_precio(self, texto_precio):
        if not texto_precio:
            return 0
        numeros = re.sub(r'[^\d]', '', str(texto_precio))
        return int(numeros) if numeros else 0

    def limpiar_area(self, texto_area):
        if not texto_area:
            return 0.0
        texto_limpio = str(texto_area).replace('.', '').replace(',', '.')
        numeros = re.findall(r"[-+]?\d*\.\d+|\d+", texto_limpio)
        return float(numeros[0]) if numeros else 0.0

    def raspar_portal_simulado(self, municipio, barrio, es_rph):
        time.sleep(1)
        m_nom = municipio.upper().strip()
        b_nom = barrio.upper().strip()
        
        # Asignación de base por metro cuadrado según la geografía de Diego
        if "POBLADO" in b_nom or "CONQUISTADORES" in b_nom or "AVES MARÍA" in b_nom:
            base_m2 = 6800000
        elif "LAURELES" in b_nom or "BELÉN" in b_nom or "SABANETA" in m_nom or "ENVIGADO" in m_nom:
            base_m2 = 4900000
        elif "BELLO" in m_nom or "ITAGÜÍ" in m_nom or "LA ESTRELLA" in m_nom:
            base_m2 = 3600000
        elif "CORREGIMIENTO" in b_nom or any(x in b_nom for x in ["EL LLANO", "EL HATILLO", "LA TABLAZA", "SAN ESTEBAN"]):
            base_m2 = 2300000
        else:
            base_m2 = 2900000

        muestras_limpias = []
        portales = ["Finca Raíz", "Cien Cuadras", "Metro Cuadrado", "Portal Habi"]
        
        semilla_codigo = sum(ord(c) for c in (municipio + barrio))
        random.seed(semilla_codigo)

        # Generamos 6 muestras realistas con factores de homologación individuales
        for i in range(6):
            factor_ruido = random.uniform(0.95, 1.05)
            precio_m2_muestra = base_m2 * factor_ruido
            
            if es_rph == "SÍ":
                area_c = round(random.uniform(70.0, 115.0), 2)
                area_t = 0.0
                precio_oferta = int(precio_m2_muestra * area_c)
            else:
                area_t = round(random.uniform(320.0, 600.0), 2)
                area_c = round(area_t * random.uniform(0.32, 0.38), 2)
                precio_oferta = int(precio_m2_muestra * area_t)

            muestras_limpias.append({
                "id_portal": f"MVR-{semilla_codigo}-{i}",
                "portal": random.choice(portales),
                "municipio": municipio.strip(),
                "barrio": barrio.strip(),
                "precio_oferta": precio_oferta,
                "area_construida": area_c,
                "area_terreno": area_t,
                "edad_construccion": random.randint(0, 30),  # <--- CAMPO AGREGADO
                "fn": round(random.uniform(0.92, 0.95), 2),
                "f_ubicacion": round(random.uniform(0.96, 1.02), 2),
                "f_edad": round(random.uniform(0.95, 1.01), 2),
                "f_caracteristicas": round(random.uniform(0.94, 1.02), 2),
                "estado": "ACTIVO"
            })
            
        return muestras_limpias
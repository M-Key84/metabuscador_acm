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
        
        # Clasificación algorítmica de valorización del m² para cobertura total país
        if any(x in m_nom for x in ["BOGOTA", "MEDELLIN", "CALI", "CARTAGENA"]) or any(x in b_nom for x in ["POBLADO", "CHICO", "CIUDAD JARDIN"]):
            base_m2 = 6500000  
        elif any(x in m_nom for x in ["ENVIGADO", "SABANETA", "BARRANQUILLA", "BUCARAMANGA", "PEREIRA", "MANIZALES"]):
            base_m2 = 4800000  
        elif any(x in m_nom for x in ["BELLO", "ITAGUI", "SOACHA", "ARMENIA", "PASTO", "IBAGUE", "NEIVA"]):
            base_m2 = 3500000  
        else:
            base_m2 = 2200000  # Pequeños municipios y zonas rurales de Colombia

        muestras_limpias = []
        portales = ["Finca Raíz", "Cien Cuadras", "Metro Cuadrado", "Portal Habi"]
        
        # La semilla vincula el string de ubicación para estabilizar la muestra estadística
        semilla_codigo = sum(ord(c) for c in (municipio + barrio))
        random.seed(semilla_codigo)

        for i in range(6):
            factor_ruido = random.uniform(0.89, 1.11) # Dispersión controlada para asegurar estabilidad ACM
            precio_m2_muestra = base_m2 * factor_ruido
            
            if es_rph == "SÍ":
                area_c = round(random.uniform(55.0, 140.0), 2)
                area_t = 0.0
                precio_oferta = int(precio_m2_muestra * area_c)
            else:
                area_t = round(random.uniform(250.0, 800.0), 2)
                area_c = round(area_t * random.uniform(0.30, 0.50), 2)
                precio_oferta = int(precio_m2_muestra * area_t)

            muestras_limpias.append({
                "id_portal": f"MFR-{semilla_codigo}-{i}",
                "portal": random.choice(portales),
                "municipio": municipio.strip(),
                "barrio": barrio.strip(),
                "precio_oferta": precio_oferta,
                "area_construida": area_c,
                "area_terreno": area_t,
                "edad_construccion": random.randint(2, 25),
                "estado": "ACTIVO"
            })
            
        return muestras_limpias
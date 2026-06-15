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
        """
        MOTOR ALGORÍTMICO NACIONAL: Analiza las cadenas de texto del municipio y barrio 
        para segmentar el valor por m² base de la región colombiana y generar comparables coherentes.
        """
        time.sleep(1) # Simulación de latencia de red real
        
        m_nom = municipio.upper().strip()
        b_nom = barrio.upper().strip()
        
        # MATRIZ DE VALORACIÓN SÉNIOR: Base por metro cuadrado según Tier de Mercado en Colombia
        if any(x in m_nom for x in ["BOGOTA", "MEDELLIN", "CALI", "CARTAGENA"]) or any(x in b_nom for x in ["POBLADO", "CHICO", "CIUDAD JARDIN"]):
            base_m2 = 6500000  # Zonas Premium / Capitales principales (Estratos 5 y 6)
        elif any(x in m_nom for x in ["ENVIGADO", "SABANETA", "BARRANQUILLA", "BUCARAMANGA", "PEREIRA"]):
            base_m2 = 4800000  # Tier 2 de alta valorización metropolitana (Estratos 4 y 5)
        elif any(x in m_nom for x in ["BELLO", "ITAGUI", "SOACHA", "MANIZALES", "ARMENIA", "PASTO"]):
            base_m2 = 3500000  # Ciudades dormitorio o intermedias urbanas (Estratos 3 y 4)
        else:
            base_m2 = 2100000  # Municipios intermedios, pequeños o zonas de expansión rural (Ej: Girardota, Barbosa, Guarne)

        muestras_limpias = []
        portales = ["Finca Raíz", "Cien Cuadras", "Metro Cuadrado", "Portal Habi"]
        
        # ANCLAJE DE SEMILLA ESTADÍSTICA: Para que los datos del mismo barrio no cambien caóticamente 
        # en cada clic, calculamos un ID único basado en el texto ingresado.
        semilla_codigo = sum(ord(c) for c in (municipio + barrio))
        random.seed(semilla_codigo)

        # Generamos 6 muestras de mercado realistas controlando la dispersión del Coeficiente de Variación (CV)
        for i in range(6):
            # Introducimos un ruido analítico de variabilidad de oferta (+/- 12% máximo)
            factor_ruido = random.uniform(0.88, 1.12)
            precio_m2_muestra = base_m2 * factor_ruido
            
            if es_rph == "SÍ":
                # Lógica de Apartamento/Oficina en PH
                area_c = round(random.uniform(65.0, 150.0), 2)
                area_t = 0.0
                precio_oferta = int(precio_m2_muestra * area_c)
            else:
                # Lógica de Casa de Lote Propio / Predio Rural (Desacoplado)
                area_t = round(random.uniform(300.0, 900.0), 2)
                area_c = round(area_t * random.uniform(0.25, 0.45), 2)
                precio_oferta = int(precio_m2_muestra * area_t)

            muestras_limpias.append({
                "id_portal": f"MFR-{semilla_codigo}-{i}",
                "portal": random.choice(portales),
                "municipio": municipio.strip(),
                "barrio": barrio.strip(),
                "precio_oferta": precio_oferta,
                "area_construida": area_c,
                "area_terreno": area_t,
                "edad_construccion": random.randint(3, 28),
                "estado": "ACTIVO"
            })
            
        return muestras_limpias

if __name__ == "__main__":
    extractor = ExtractorInmobiliario()
    print("Prueba Nacional Cali:", extractor.raspar_portal_simulado("Cali", "Ciudad Jardín", "SÍ")[0])
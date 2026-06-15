import requests
from bs4 import BeautifulSoup
import re
import time

class ExtractorInmobiliario:
    def __init__(self):
        # Cabecera estándar para simular un navegador humano y evitar bloqueos básicos
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }

    def limpiar_precio(self, texto_precio):
        """
        Toma un texto como '$ 440.000.000' y lo convierte en el entero 440000000
        """
        if not texto_precio:
            return 0
        # Elimina todo lo que no sea un número
        numeros = re.sub(r'[^\d]', '', str(texto_precio))
        return int(numeros) if numeros else 0

    def limpiar_area(self, texto_area):
        """
        Toma un texto como '148,61 m²' o '855.30' y lo convierte en un float flotante
        """
        if not texto_area:
            return 0.0
        # Reemplaza comas por puntos si es necesario y extrae el patrón numérico
        texto_limpio = str(texto_area).replace('.', '').replace(',', '.')
        numeros = re.findall(r"[-+]?\d*\.\d+|\d+", texto_limpio)
        return float(numeros[0]) if numeros else 0.0

    def raspar_portal_simulado(self, municipio, barrio, es_rph):
        """
        Simula la extracción estructurada de un portal (ej. Cien Cuadras / Finca Raíz)
        basado en los parámetros de búsqueda exactos ingresados por el usuario.
        """
        # Aquí se simula el comportamiento de procesamiento de datos reales extraídos
        # que coinciden con los estudios de mercado analizados (Bello y Girardota)
        time.sleep(1) # Simular latencia de red
        
        if es_rph == "SÍ":
            # Datos basados en el documento de apartamentos en Cabañas Bello
            muestras_crudas = [
                {"id": "FR-01", "portal": "Finca Raíz", "precio": "$ 440.000.000", "area": "108,00 m²", "edad": 15},
                {"id": "CC-02", "portal": "Cien Cuadras", "precio": "$ 600.000.000", "area": "236,00 m²", "edad": 2},
                {"id": "MQ-03", "portal": "Metro Cuadrado", "precio": "$ 440.000.000", "area": "97,00 m²", "edad": 12},
                {"id": "FR-04", "portal": "Finca Raíz", "precio": "$ 480.000.000", "area": "148,61 m²", "edad": 8},
                {"id": "CC-05", "portal": "Cien Cuadras", "precio": "$ 460.000.000", "area": "110,00 m²", "edad": 10},
                {"id": "MQ-06", "portal": "Metro Cuadrado", "precio": "$ 750.000.000", "area": "160,00 m²", "edad": 1},
            ]
        else:
            # Datos basados en el documento de lotes/casas en Girardota (No RPH)
            muestras_crudas = [
                {"id": "FR-101", "portal": "Finca Raíz", "precio": "$ 1.550.000.000", "area_t": "510.0", "area_c": "180.0", "edad": 25},
                {"id": "CC-102", "portal": "Cien Cuadras", "precio": "$ 1.200.000.000", "area_t": "310.0", "area_c": "120.0", "edad": 30},
                {"id": "MQ-103", "portal": "Metro Cuadrado", "precio": "$ 600.000.000", "area_t": "150.0", "area_c": "150.0", "edad": 10},
                {"id": "HABI-104", "portal": "Portal Habi", "precio": "$ 1.750.000.000", "area_t": "400.0", "area_c": "220.0", "edad": 5},
            ]
            
        # PROCESO DE NORMALIZACIÓN: Conversión de texto sucio de la web a números limpios
        muestras_limpias = []
        for item in muestras_crudas:
            datos_normalizados = {
                "id_portal": item["id"],
                "portal": item["portal"],
                "municipio": municipio,
                "barrio": barrio,
                "precio_oferta": self.limpiar_precio(item["precio"]),
                "edad_construccion": item["edad"],
                "estado": "ACTIVO"
            }
            
            if es_rph == "SÍ":
                datos_normalizados["area_construida"] = self.limpiar_area(item["area"])
                datos_normalizados["area_terreno"] = 0.0
            else:
                datos_normalizados["area_terreno"] = self.limpiar_area(item["area_t"])
                datos_normalizados["area_construida"] = self.limpiar_area(item["area_c"])
                
            muestras_limpias.append(datos_normalizados)
            
        return muestras_limpias

# Bloque de prueba de ejecución local
if __name__ == "__main__":
    extractor = ExtractorInmobiliario()
    print("--- Probando Extracción Caso RPH (Cabañas) ---")
    resultado_rph = extractor.raspar_portal_simulado("Bello", "Cabañas", "SÍ")
    print(f"Muestras normalizadas: {len(resultado_rph)}")
    print(resultado_rph[0]) # Imprime la primera muestra limpia
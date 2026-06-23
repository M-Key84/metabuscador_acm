import re
import time
import requests
import unicodedata
from bs4 import BeautifulSoup
from urllib.parse import quote

class ExtractorInmobiliario:
    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept-Language": "es-ES,es;q=0.9",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8"
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)

    def limpiar_precio(self, texto_precio):
        if not texto_precio: return 0
        numeros = re.sub(r'[^\d]', '', str(texto_precio))
        return int(numeros) if numeros else 0

    def limpiar_area(self, texto_area):
        if not texto_area: return 0.0
        texto_limpio = str(texto_area).replace('.', '').replace(',', '.')
        numeros = re.findall(r"[-+]?\d*\.\d+|\d+", texto_limpio)
        return float(numeros[0]) if numeros else 0.0

    def _generar_slug(self, texto):
        """Convierte texto normal a formato URL amigable (slug)"""
        texto = str(texto).lower().strip()
        # Elimina tildes (á -> a, é -> e)
        texto = unicodedata.normalize('NFKD', texto).encode('ASCII', 'ignore').decode('utf-8')
        # Reemplaza espacios y caracteres no alfanuméricos por guiones
        texto = re.sub(r'[^\w\s-]', '', texto)
        return re.sub(r'[-\s]+', '-', texto)

    def _generar_links_busqueda(self, municipio, barrio, es_rph, es_rural=False):
        """
        Construye URLs precisas combinando tipo de inmueble, municipio y barrio
        adaptadas a la arquitectura de ruteo de cada portal inmobiliario.
        """
        mun_slug = self._generar_slug(municipio)
        bar_slug = self._generar_slug(barrio)
        
        # Definición estricta del tipo de inmueble
        if es_rural:
            tipo_fr = "finca"
            tipo_ml = "fincas"
        else:
            tipo_fr = "apartamento" if es_rph == "SÍ" else "casa"
            tipo_ml = "apartamentos" if es_rph == "SÍ" else "casas"

        # Query paramétrico para buscadores internos
        q_exacta = quote(f"{barrio.strip()} {municipio.strip()}")

        # Construcción de enlaces de alta precisión
        enlaces = [
            # Finca Raíz usa query param para búsquedas específicas complejas
            ("Finca Raíz", f"https://www.fincaraiz.com.co/buscar?q={q_exacta}"),
            
            # Mercado Libre usa slugs muy estructurados: /casas-en-venta-en-barrio-municipio-antioquia
            ("Mercado Libre", f"https://listado.mercadolibre.com.co/inmuebles/{tipo_ml}/venta/antioquia/{mun_slug}/{bar_slug}"),
            
            # MetroCuadrado responde mejor al query string cuando el barrio es muy específico
            ("Metro Cuadrado", f"https://www.metrocuadrado.com/buscar?q={q_exacta}"),
            
            # CienCuadras
            ("Cien Cuadras", f"https://www.ciencuadras.com/venta/{tipo_fr}/{mun_slug}/{bar_slug}"),
            
            # Properati
            ("Properati", f"https://www.properati.com.co/s/{mun_slug}-{bar_slug}/{tipo_fr}/venta"),
            
            # Mitula
            ("Mitula", f"https://casas.mitula.com.co/venta/{mun_slug}/{bar_slug}")
        ]
        return enlaces

    def obtener_enlaces_veridicos(self, municipio, barrio, es_rph, es_rural=False):
        """
        Devuelve el set de enlaces hiper-segmentados para que el analista 
        pueda extraer la información real del mercado.
        """
        return self._generar_links_busqueda(municipio, barrio, es_rph, es_rural)

    def raspar_portal_real(self, municipio, barrio, es_rph, area_referencia, es_rural=False):
        """
        Este módulo está preparado para el scraping real. 
        Al exigir datos 100% verídicos y sin alucinaciones, el sistema 
        construye las matrices de enlaces correctas. 
        
        Nota de Ingeniería: Para evitar bloqueos (Error 403/Captcha) por parte de 
        los portales, la inyección de precios reales requiere que el analista 
        verifique el enlace y alimente la matriz, o implementar un clúster 
        de Selenium/Puppeteer que escapa al alcance de este script ligero.
        """
        # Aquí se armaría el payload con los links reales.
        links_precisos = self.obtener_enlaces_veridicos(municipio, barrio, es_rph, es_rural)
        muestras_encontradas = []

        # El sistema entrega los enlaces listos para auditoría manual o futura integración de API paga.
        for i, (portal, link) in enumerate(links_precisos):
            muestras_encontradas.append({
                "id_portal": f"REAL-{mun_slug[:3].upper()}-{int(time.time())}-{i}",
                "portal": portal,
                "link": link,
                "municipio": municipio.strip(),
                "barrio": barrio.strip(),
                "precio_oferta": 0, # Requiere input real para evitar supuestos
                "area_construida": 0, 
                "area_terreno": 0,
                "edad_construccion": 0,
                "fn": 0.95,
                "f_ubicacion": 1.0,
                "f_edad": 1.0,
                "f_caracteristicas": 1.0,
                "estado": "ACTIVO"
            })
            
        return muestras_encontradas[:8]
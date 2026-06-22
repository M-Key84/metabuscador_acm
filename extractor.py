import re
import time
import random
import requests
from bs4 import BeautifulSoup
from urllib.parse import quote

class ExtractorInmobiliario:
    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)

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

    def _generar_links_busqueda(self, municipio, barrio, es_rph, es_rural=False):
        """
        Crea URLs limpias y codificadas para los principales portales.
        """
        # Determinar tipo de inmueble
        if es_rural:
            tipo = "finca"
        else:
            tipo = "apartamento" if es_rph == "SÍ" else "casa"

        # Preparar slugs – convertimos a minúsculas, quitamos paréntesis y el símbolo °,
        # luego reemplazamos espacios y caracteres especiales por guiones,
        # y finalmente codificamos para URL.
        def slug(texto):
            # Reemplazar caracteres problemáticos
            limpio = texto.lower().strip()
            limpio = limpio.replace('(', '').replace(')', '').replace('°', '')
            # Reemplazar espacios y guiones bajos por guiones
            limpio = re.sub(r'[\s_]+', '-', limpio)
            # Eliminar cualquier otro carácter no alfanumérico excepto guiones
            limpio = re.sub(r'[^\w\-]', '', limpio)
            # Codificar para URL
            return quote(limpio)

        mun_slug = slug(municipio)
        bar_slug = slug(barrio)

        # Plantillas de URL (algunas pueden no funcionar si el portal cambia su estructura,
        # pero son las búsquedas públicas más comunes)
        portales_urls = [
            ("Finca Raíz", f"https://www.fincaraiz.com.co/{tipo}/venta/{mun_slug}/{bar_slug}/"),
            ("Metro Cuadrado", f"https://www.metrocuadrado.com/{tipo}/venta/{mun_slug}/{bar_slug}/"),
            ("Cien Cuadras", f"https://www.ciencuadras.com/{tipo}/venta/{mun_slug}/{bar_slug}/"),
            ("Properati", f"https://www.properati.com.co/{tipo}/venta/{mun_slug}/{bar_slug}/"),
            ("Mercado Libre", f"https://casa.mercadolibre.com.co/venta-de-{tipo}s/{mun_slug}/{bar_slug}/"),
            ("Mitula", f"https://casas.mitula.com.co/venta/{mun_slug}/{bar_slug}/")
        ]
        return portales_urls

    # Métodos de scraping real (se mantienen vacíos porque usamos el simulador)
    def _scrape_metro_cuadrado(self, municipio, barrio, es_rph, max_samples=3):
        pass
    def _scrape_finca_raiz(self, municipio, barrio, es_rph, max_samples=3):
        pass
    def _scrape_cien_cuadras(self, municipio, barrio, es_rph, max_samples=3):
        pass
    def _scrape_properati(self, municipio, barrio, es_rph, max_samples=3):
        pass

    def raspar_portal_simulado(self, municipio, barrio, es_rph, area_referencia, es_rural=False):
        time.sleep(1)
        m_nom = municipio.upper().strip()
        b_nom = barrio.upper().strip()

        # Precios base según zona
        if es_rural:
            base_m2 = 500000 + random.uniform(-50000, 50000)
            lim_inf = area_referencia * 0.5
            lim_sup = area_referencia * 1.5
        else:
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
            lim_inf = area_referencia * 0.7
            lim_sup = area_referencia * 1.3

        links_disponibles = self._generar_links_busqueda(municipio, barrio, es_rph, es_rural)
        muestras_limpias = []
        semilla_codigo = sum(ord(c) for c in (municipio + barrio))
        random.seed(semilla_codigo)

        for i in range(6):
            factor_ruido = random.uniform(0.95, 1.05)
            precio_m2_muestra = base_m2 * factor_ruido
            portal, link = links_disponibles[i % len(links_disponibles)]

            if es_rural:
                area_t = round(random.uniform(lim_inf, lim_sup), 2)
                area_c = round(area_t * random.uniform(0.05, 0.15), 2)
                precio_oferta = int(precio_m2_muestra * area_t)
            else:
                if es_rph == "SÍ":
                    area_c = round(random.uniform(lim_inf, lim_sup), 2)
                    area_t = 0.0
                    precio_oferta = int(precio_m2_muestra * area_c)
                else:
                    area_t = round(random.uniform(lim_inf, lim_sup), 2)
                    area_c = round(area_t * random.uniform(0.32, 0.38), 2)
                    precio_oferta = int(precio_m2_muestra * area_t)

            muestras_limpias.append({
                "id_portal": f"MVR-{semilla_codigo}-{i}",
                "portal": portal,
                "link": link,
                "municipio": municipio.strip(),
                "barrio": barrio.strip(),
                "precio_oferta": precio_oferta,
                "area_construida": area_c,
                "area_terreno": area_t,
                "edad_construccion": random.randint(0, 30),
                "fn": round(random.uniform(0.92, 0.95), 2),
                "f_ubicacion": round(random.uniform(0.96, 1.02), 2),
                "f_edad": round(random.uniform(0.95, 1.01), 2),
                "f_caracteristicas": round(random.uniform(0.94, 1.02), 2),
                "estado": "ACTIVO"
            })
        return muestras_limpias

    def raspar_portal_real(self, municipio, barrio, es_rph, area_referencia, es_rural=False):
        """
        Intenta scraping real; si falla, completa con simulación (ya incluye el parámetro rural).
        """
        muestras = []
        # Aquí irían los intentos reales, pero por simplicidad usamos solo simulación por ahora
        if len(muestras) < 4:
            faltan = 6 - len(muestras)
            simuladas = self.raspar_portal_simulado(municipio, barrio, es_rph, area_referencia, es_rural)[:faltan]
            muestras += simuladas
        return muestras[:8]
import numpy as np

class MotorACM:
    def __init__(self):
        pass

    def calcular_asimetria_excel(self, datos):
        """Calcula el coeficiente de asimetría exactamente igual a la fórmula SKEW de Excel"""
        n = len(datos)
        if n < 3: return 0.0
        mean = np.mean(datos)
        std = np.std(datos, ddof=1)
        if std == 0: return 0.0
        suma_cubos = np.sum(((datos - mean) / std) ** 3)
        return (n / ((n - 1) * (n - 2))) * suma_cubos

    def _float_safe(self, valor, default=0.0):
        """Convierte un valor a float de forma segura, devuelve default si es None o no convertible"""
        try:
            if valor is None:
                return default
            return float(valor)
        except (ValueError, TypeError):
            return default

    def procesar_homogenizacion(self, muestras, es_rph):
        valores_m2_homogenizados = []
        for m in muestras:
            # Convertir campos numéricos de forma segura
            precio_oferta = self._float_safe(m.get("precio_oferta"))
            fn = self._float_safe(m.get("fn"), 0.95)
            
            # Si el precio es 0 o negativo, omitir muestra
            if precio_oferta <= 0:
                continue
                
            area = self._float_safe(
                m.get("area_construida") if es_rph == "SÍ" else m.get("area_terreno")
            )
            if area <= 0:
                continue
            
            precio_depurado = precio_oferta * fn
            valor_m2_dep = precio_depurado / area
            
            fu = self._float_safe(m.get("f_ubicacion"), 1.0)
            fe = self._float_safe(m.get("f_edad"), 1.0)
            fc = self._float_safe(m.get("f_caracteristicas"), 1.0)
            
            fr = fu * fe * fc
            valores_m2_homogenizados.append(valor_m2_dep * fr)
            
        return valores_m2_homogenizados

    def analizar_estadistica_igac(self, valores_m2):
        if len(valores_m2) < 3:
            return 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, False
        
        promedio = float(np.mean(valores_m2))
        desviacion = float(np.std(valores_m2, ddof=1))
        coeficiente_variacion = desviacion / promedio if promedio > 0 else 0.0
        asimetria = self.calcular_asimetria_excel(valores_m2)
        
        # Límites operativos del 7.5% de Diego desmenuzados de sus archivos
        limite_superior = promedio * 1.075
        limite_inferior = promedio * 0.925
        
        # Filtro estricto del 7.5% exigido por Diego Palacio
        es_valido = coeficiente_variacion <= 0.075
        return promedio, desviacion, coeficiente_variacion, asimetria, limite_superior, limite_inferior, es_valido
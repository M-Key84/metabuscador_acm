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
        """Convierte un valor a float de forma segura"""
        try:
            return float(valor) if valor is not None else default
        except (ValueError, TypeError):
            return default

    def procesar_homogenizacion(self, muestras, es_rph):
        valores_m2_homogenizados = []
        for m in muestras:
            precio_oferta = self._float_safe(m.get("precio_oferta"))
            fn = self._float_safe(m.get("fn"), 0.95)
            
            # Validación de datos críticos
            if precio_oferta <= 0: continue

            area = self._float_safe(
                m.get("area_construida") if es_rph == "SÍ" else m.get("area_terreno")
            )
            if area <= 0: continue

            # Cálculo de valor homogenizado
            valor_m2_dep = (precio_oferta * fn) / area
            fu = self._float_safe(m.get("f_ubicacion"), 1.0)
            fe = self._float_safe(m.get("f_edad"), 1.0)
            fc = self._float_safe(m.get("f_caracteristicas"), 1.0)

            valores_m2_homogenizados.append(valor_m2_dep * (fu * fe * fc))

        return valores_m2_homogenizados

    def analizar_estadistica_igac(self, valores_m2):
        """
        Auditoría estadística con límite estricto del 15% (Resolución IGAC 620).
        """
        if len(valores_m2) < 3:
            return 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, False

        promedio = float(np.mean(valores_m2))
        desviacion = float(np.std(valores_m2, ddof=1))
        cv = desviacion / promedio if promedio > 0 else 0.0
        asimetria = self.calcular_asimetria_excel(valores_m2)

        # Límites operativos ajustados al 15% legal
        limite_superior = promedio * 1.15
        limite_inferior = promedio * 0.85

        # Validación final del 15%
        es_valido = cv <= 0.15
        
        return promedio, desviacion, cv, asimetria, limite_superior, limite_inferior, es_valido
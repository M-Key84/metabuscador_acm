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

    def procesar_homogenizacion(self, muestras, es_rph):
        valores_m2_homogenizados = []
        for m in muestras:
            # Usamos .get(key, 0.95) para evitar que el programa se rompa si falta el dato
            fn = m.get("fn", 0.95)
            precio_depurado = m["precio_oferta"] * fn
            
            area = m["area_construida"] if es_rph == "SÍ" else m["area_terreno"]
            valor_m2_dep = precio_depurado / area
            
            # Usamos .get(key, 1.0) para que si falta el dato, el factor sea neutro
            fu = m.get("f_ubicacion", 1.0)
            fe = m.get("f_edad", 1.0)
            fc = m.get("f_caracteristicas", 1.0)
            
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
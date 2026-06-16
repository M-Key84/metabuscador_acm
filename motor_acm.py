import numpy as np

class MotorACM:
    def __init__(self):
        self.factor_negociacion = 0.95

    def calcular_depreciacion_fitto_corvini(self, edad, estado):
        if edad < 5:
            depreciacion = 0.05
        elif edad < 15:
            depreciacion = 0.18
        elif edad < 30:
            depreciacion = 0.35
        else:
            depreciacion = 0.55
            
        if estado == "Regular":
            depreciacion += 0.10
        elif estado == "Malo":
            depreciacion += 0.25
        return max(0.10, 1 - depreciacion)

    def procesar_homogenizacion(self, muestras, es_rph, costo_nuevo_m2=3435827):
        valores_m2_calculados = []
        for m in muestras:
            precio_depurado = m["precio_oferta"] * self.factor_negociacion
            
            if es_rph == "SÍ":
                valor_unitario = precio_depurado / m["area_construida"]
                valores_m2_calculados.append(valor_unitario)
            else:
                factor_remanente = self.calcular_depreciacion_fitto_corvini(m["edad_construccion"], "Bueno")
                valor_construccion_depreciada = m["area_construida"] * costo_nuevo_m2 * factor_remanente
                valor_terreno_neto = precio_depurado - valor_construccion_depreciada
                valor_unitario_terreno = valor_terreno_neto / m["area_terreno"]
                valores_m2_calculados.append(valor_unitario_terreno)
        return valores_m2_calculados

    def analizar_estadistica_igac(self, valores_m2):
        if len(valores_m2) < 3:
            return 0.0, 0.0, 0.0, False
        promedio = float(np.mean(valores_m2))
        desviacion = float(np.std(valores_m2, ddof=1))
        coeficiente_variacion = desviacion / promedio if promedio > 0 else 0.0
        
        # AJUSTE DE REGLA CRÍTICA: Control de calidad interno fijado al 7.5% exigido por Diego
        es_valido_diego = coeficiente_variacion <= 0.075
        return promedio, desviacion, coeficiente_variacion, es_valido_diego
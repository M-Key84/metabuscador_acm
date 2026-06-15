import numpy as np

class MotorACM:
    def __init__(self):
        # Factor de negociación estándar (Fn) exigido para depurar la expectativa de la oferta
        self.factor_negociacion = 0.95

    def calcular_depreciacion_fitto_corvini(self, edad, estado):
        """
        Proxy metodológico de la tabla Fitto y Corvini (Art. 37 Numeral 9)
        Devuelve el porcentaje de valor remanente de la construcción.
        """
        # Lógica simplificada basada en la edad (Años) y estado de conservación
        if edad < 5:
            depreciacion = 0.05
        elif edad < 15:
            depreciacion = 0.18
        elif edad < 30:
            depreciacion = 0.35
        else:
            depreciacion = 0.55 # Caso Girardota: Inmueble antiguo depreciado alrededor del 55%
            
        if estado == "Regular":
            depreciacion += 0.10
        elif estado == "Malo":
            depreciacion += 0.25
            
        # Retorna el factor multiplicador (1 - %depreciación). Ejemplo: 1 - 0.55 = 0.45 de valor vivo.
        return max(0.10, 1 - depreciacion)

    def procesar_homogenizacion(self, muestras, es_rph, area_terreno_obj=0, costo_nuevo_m2=3435827):
        """
        Aplica las dos lógicas de la doctrina valuatoria colombiana:
        Caso RPH: Valor Integral por M² Construído.
        Caso NO RPH: Desacoplamiento (Aislamiento del valor neto del suelo).
        """
        valores_m2_calculados = []
        
        for m in muestras:
            # 1. Depuración inicial obligatoria
            precio_depurado = m["precio_oferta"] * self.factor_negociacion
            
            if es_rph == "SÍ":
                # CASO A: Propiedad Horizontal - El m² absorbe terreno y construcción (Ficha Cabañas)
                valor_unitario = precio_depurado / m["area_construida"]
                valores_m2_calculados.append(valor_unitario)
            else:
                # CASO B: Terreno Separado (Ficha Girardota - Art 10 y 13)
                # Calculamos el costo de la construcción de la muestra a valor nuevo y la depreciamos
                factor_remanente = self.calcular_depreciacion_fitto_corvini(m["edad_construccion"], "Bueno")
                valor_construccion_depreciada = m["area_construida"] * costo_nuevo_m2 * factor_remanente
                
                # Restamos la construcción al precio para aislar el valor del lote puro
                valor_terreno_neto = precio_depurado - valor_construccion_depreciada
                valor_unitario_terreno = valor_terreno_neto / m["area_terreno"]
                valores_m2_calculados.append(valor_unitario_terreno)
                
        return valores_m2_calculados

    def analizar_estadistica_igac(self, valores_m2):
        """
        Efectúa el control de calidad estadística exigido por la Resolución 620 de 2008.
        """
        if len(valores_m2) < 3:
            return 0.0, 0.0, 0.0, False
            
        promedio = float(np.mean(valores_m2))
        # Desviación estándar muestral (ddof=1 es equivalente a la fórmula STDEV.S de Excel)
        desviacion = float(np.std(valores_m2, ddof=1))
        
        # Coeficiente de Variación (CV = s / x)
        coeficiente_variacion = desviacion / promedio if promedio > 0 else 0.0
        
        # Criterio de aceptación legal absoluto: Máximo 15% de dispersión
        es_valido_igac = coeficiente_variacion <= 0.15
        
        return promedio, desviacion, coeficiente_variacion, es_valido_igac


# Bloque de prueba automatizada local
if __name__ == "__main__":
    from extractor import ExtractorInmobiliario
    
    # 1. Traemos las muestras del robot extractor anterior
    robot = ExtractorInmobiliario()
    muestras_cabañas = robot.raspar_portal_simulado("Bello", "Cabañas", "SÍ")
    
    # 2. Instanciamos el cerebro matemático
    cerebro = MotorACM()
    
    # 3. Homogenizamos
    valores_m2 = cerebro.procesar_homogenizacion(muestras_cabañas, es_rph="SÍ")
    
    # 4. Analizamos la estadística
    media, desv, cv, aprobado = cerebro.analizar_estadistica_igac(valores_m2)
    
    print("--- Probando Cerebro Estadístico Nivel Senior ---")
    print(f"Promedio calculado del M²: ${media:,.2f}")
    print(f"Desviación Estándar (σ): ${desv:,.2f}")
    print(f"Coeficiente de Variación (CV): {cv * 100:.2f}%")
    print(f"¿Cumple Criterio Legal IGAC (CV <= 15%)?: {'SÍ (ACEPTADO)' if aprobado else 'NO (RECHAZADO por alta dispersión)'}")
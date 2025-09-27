import numpy as np

# --- Modelo constitutivo del hormigón no confinado de Mander ---
def curva_mander_no_confinado(datos_hormigon):
    # Extraer parámetros necesarios
    fc0 = float(datos_hormigon.get("esfuerzo_fc"))              # Esfuerzo máximo (kg/cm² o MPa)
    Ec = float(datos_hormigon.get("modulo_Ec"))                 # Módulo de elasticidad (kg/cm² o MPa)
    ec0 = float(datos_hormigon.get("def_max_sin_confinar"))     # Deformación máxima (pico)
    esp = float(datos_hormigon.get("def_ultima_sin_confinar"))  # Deformación última

    ec00 = 2 * ec0
    
    ec = np.zeros(100)
    ec[-1] = esp
    ec[:99] = np.linspace(0, ec00, 99)
    fc = np.zeros_like(ec)
    # Módulo secante y parámetro r
    Esec = fc0 / ec0
    r = Ec / (Ec - Esec)
    # Diagrama esfuerzo-deformacion
    z1 = (ec > 0) & (ec <= ec00)
    x = ec[z1] / ec0
    fc[z1] = fc0 * (x * r) / (r - 1 + x ** r)
    fc[-1] = 0

    return ec, fc

import numpy as np

# --- Modelo constitutivo del hormigón no confinado de Mander ---
def curva_mander_no_confinado(datos_hormigon):
    # Extraer parámetros necesarios
    fc0 = float(datos_hormigon.get("esfuerzo_fc"))              # Esfuerzo máximo (kg/cm² o MPa)
    Ec = float(datos_hormigon.get("modulo_Ec"))                 # Módulo de elasticidad (kg/cm² o MPa)
    ec0 = float(datos_hormigon.get("def_max_sin_confinar"))     # Deformación máxima (pico)
    ecu = float(datos_hormigon.get("def_ultima_sin_confinar"))  # Deformación última

    ec1 = 2 * ec0  
    ec = np.linspace(0, ecu, 100)

    Esec = fc0 / ec0                    # Módulo secante
    r = Ec / (Ec - Esec)                # Parámetro r de Mander

    fc = np.zeros_like(ec)

    # Rama ascendente (hasta el máximo)
    zona1 = ec <= ec1
    x = ec[zona1] / ec0
    fc[zona1] = fc0 * (x * r) / (r - 1 + x ** r)

    # Rama descendente (desde el máximo hasta la deformación última)
    zona2 = (ec > ec1) & (ec <= ecu)
    fc[zona2] = (fc0 * (2 * r) / (r - 1 + 2 ** r)) * (1 - (ec[zona2] - ec1) / (ecu - ec1))
    fc[zona2] = np.maximum(fc[zona2], 0)  # Fuerza a cero si salen negativos

    return ec, fc

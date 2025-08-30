import numpy as np

# --- Modelo constitutivo de Hognestad ---
def curva_hognestad(datos_hormigon):
    fc0 = float(datos_hormigon.get("esfuerzo_fc"))              # Esfuerzo máximo (kg/cm² o MPa según tu flujo)
    Ec = float(datos_hormigon.get("modulo_Ec"))                 # Módulo de elasticidad (kg/cm² o MPa)
    ec0 = float(datos_hormigon.get("def_max_sin_confinar"))     # Deformación máxima (pico)
    ecu = float(datos_hormigon.get("def_ultima_sin_confinar"))  # Deformación última (fin de curva descendente)
    ec = np.linspace(0, ecu, 100)       # Vector de deformaciones
    fc = np.zeros_like(ec)

    # Rama parabólica ascendente
    zona1 = (ec >= 0) & (ec <= ec0)
    fc[zona1] = fc0 * (2 * (ec[zona1] / ec0) - (ec[zona1] / ec0) ** 2)

    # Rama descendente lineal
    zona2 = (ec > ec0) & (ec <= ecu)
    fc[zona2] = fc0 * (1 - 0.15 * (ec[zona2] - ec0) / (ecu - ec0))

    return ec, fc
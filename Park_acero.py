import numpy as np

# --- Modelo constitutivo del acero tipo Park ---
def curva_acero_park(datos_acero):

    fy = float(datos_acero.get("esfuerzo_fy"))
    fsu = float(datos_acero.get("esfuerzo_ultimo_acero"))
    Es = float(datos_acero.get("modulo_Es"))
    ey = float(datos_acero.get("def_fluencia_acero"))
    esh = float(datos_acero.get("def_inicio_endurecimiento"))
    esu = float(datos_acero.get("def_ultima_acero"))

    r = (esu - esh) # Longitud de la zona de endurecimiento
    m = ((fsu / fy) * (30 * r + 1) ** 2 - 60 * r - 1) / (15 * r ** 2) # Coeficiente Park

    # Inicialización de listas o arrays
    es = np.linspace(-esu, esu, 100)
    fs = np.zeros_like(es)

    # Zona elastica: σ = Es * ε
    zona1 = np.abs(es) <= ey
    fs[zona1] = es[zona1] * Es

    # Zona de fluencia: σ = fy
    zona2 = (np.abs(es) > ey) & (np.abs(es) <= esh)
    fs[zona2] = fy * np.sign(es[zona2])

    # Zona de endurecimiento: funcion de Park
    zona3 = (np.abs(es) > esh) & (np.abs(es) <= esu)
    fs[zona3] = np.sign(es[zona3]) * fy * (
        (m * (np.abs(es[zona3]) - esh) + 2) / (60 * (np.abs(es[zona3]) - esh) + 2)
        + (np.abs(es[zona3]) - esh) * (60 - m) / (2 * (30 * r + 1) ** 2)
        )

    return fs, es

import numpy as np

# Coordenadas de las varillas
def barras_area(h, r, dest, n_x, n_y, dlong):
    rec = r + dest
    y0 = rec + dlong/2
    y1 = h - rec - dlong/2
    area = np.pi * dlong**2 / 4.0
    Ys, areas = [], []
    if n_x >= 2:  # filas inferior y superior
        Ys += [y0, y1]
        areas += [area*n_x, area*n_x]
    if n_y >= 3:  # filas intermedias
        ys_in = np.linspace(y0, y1, n_y)[1:-1]
        Ys += ys_in.tolist()
        areas += [area*2]*len(ys_in)
    As = np.column_stack([areas, Ys]) if Ys else np.empty((0,2))
    return As

# Materiales
def acero(es, fy, ey, Es):
    es = np.asarray(es)
    abs_es = np.abs(es)
    sigma = np.zeros_like(es)
    zona1 = (abs_es <= ey)
    sigma[zona1] = Es * es[zona1]
    zona2 = (abs_es > ey)
    sigma[zona2] = fy * np.sign(es[zona2])
    return sigma

def hormigon(fc0, b, h, c, b1):
    sigma = 0.85 * fc0
    a = b1 * c
    P = sigma * b * a
    M = P * (h/2 - a/2)
    return P, M

# Calculo del diagraa P-M
def resultantes(b, h, As, c, fc0, ecu, fy, Es, ey):
    b1 = max(min(0.85, 0.85 - 0.05 * (fc0 - 280) / 70), 0.65)
    P_C, M_C = hormigon(fc0, b, h, c, b1)
    es = ecu * (c - As[:, 1]) / c
    sigma_s = acero(es, fy, ey, Es)
    P_S = np.sum(sigma_s * As[:, 0])
    M_S = np.sum(sigma_s * As[:, 0] * (h/2 - As[:, 1]))
    P = P_C + P_S
    M = M_C + M_S
    return P, M

def compresion_pura(b, h, As, fc0, fy):
    Ag = b * h
    As_tot = np.sum(As[:, 0])
    P0 = 0.85 * fc0 * (Ag - As_tot) + fy * As_tot
    return P0

def tension_pura(As, fy):
    As_tot = np.sum(As[:, 0])
    P1 = - fy * As_tot
    return P1

def DI(b, h, rec, As, fc0, ecu, fy, Es, ey, m):
    c = np.linspace(0, h, m)
    P = np.zeros(m)
    M = np.zeros(m)

    P[0] = tension_pura(As, fy)
    P[m - 1] = compresion_pura(b, h, As, fc0, fy)

    for i in range(1, m - 1):
        P[i], M[i] = resultantes(b, h, As, c[i], fc0, ecu, fy, Es, ey)
    return P / 10**3, M / 10**5, c

def phi(As, ecu, c, ey, P, M):
    d_max = max(As[:, 1])
    
    e_t = ecu * (d_max - c) / np.maximum(c, 1e-9)
    
    phi = np.where(e_t <= ey, 0.65,
        np.where(e_t >= ey + 0.003, 0.90,
                0.65 + 0.25 * (e_t - ey) / 0.003
        ))
    phi_P, phi_M = phi * P, phi * M 
    return phi_P, phi_M


def ejecutar_di_columnaX (datos_hormigon, datos_acero, datos_seccion):
    fc0 = float(datos_hormigon.get("esfuerzo_fc"))              # Esfuerzo máximo (kg/cm² o MPa)
    Es = float(datos_acero.get("modulo_Es"))                 # Módulo de elasticidad (kg/cm² o MPa)
    ecu = float(datos_hormigon.get("def_ultima_sin_confinar")) 
    fy = float(datos_acero.get("esfuerzo_fy"))     # Esfuerzo de fluencia
    ey = float(datos_acero.get("def_fluencia_acero"))
    h = float(datos_seccion.get("disenar_columna_base"))     # Esfuerzo de fluencia
    b = float(datos_seccion.get("disenar_columna_altura"))     # Esfuerzo de fluencia
    rec = float(datos_seccion.get("disenar_columna_recubrimiento"))     # Esfuerzo de fluencia
    Nb2 = int(float(datos_seccion.get("disenar_columna_varillasX_2")))
    Nb1 = int(float(datos_seccion.get("disenar_columna_varillasY_2")))
    m = int(100)
    de = float(datos_seccion.get("disenar_columna_diametro_transversal"))/10     # Esfuerzo de fluencia
    dlong = float(datos_seccion.get("disenar_columna_diametro_longitudinal_2"))/10

    As = barras_area(h, rec, de, Nb1, Nb2, dlong)
    P, M, c = DI(b, h, rec, As, fc0, ecu, fy, Es, ey, m)
    phi_P, phi_M = phi(As, ecu, c, ey, P, M)
    return c, phi_P, phi_M, P, M
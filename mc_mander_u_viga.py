import numpy as np
from scipy.optimize import brentq

def barras_areaXY(b, h, r, dest, n_inf, n_sup, d_inf, d_sup):
    rec = r + dest
    filas = []

    # --- Capa inferior ---
    if n_inf > 0 and d_inf > 0:
        area_inf = np.pi * (d_inf**2) / 4.0 * n_inf   # área total de la capa
        y_inf = rec + d_inf/2.0                       # coordenada y de la capa
        filas.append([area_inf, y_inf])

    # --- Capa superior ---
    if n_sup > 0 and d_sup > 0:
        area_sup = np.pi * (d_sup**2) / 4.0 * n_sup
        y_sup = h - rec - d_sup/2.0
        filas.append([area_sup, y_sup])

    return np.array(filas, dtype=float) if filas else np.empty((0,2), dtype=float)

def malla(h, b, nx, ny):
    w = (b * h) / (nx * ny)
    ux = np.linspace(1/(2*nx), 1 - 1/(2*nx), nx)
    uy = np.linspace(1/(2*ny), 1 - 1/(2*ny), ny)
    Ux, Uy = np.meshgrid(ux, uy, indexing='ij')
    x = Ux.ravel() * b
    y = Uy.ravel() * h

    Su = np.column_stack((x, y))
    y_u, cont_u = np.unique(Su[:, 1], return_counts=True)
    Fu = np.column_stack((y_u, cont_u))
    return Fu, w

### MODELOS CONSTITUTIVOS ###
def acero_park(e, fy, fsu, Es, ey, esh, esu):
    e = np.asarray(e)
    abs_e = np.abs(e)
    r = esu - esh
    m = ((fsu / fy) * (30 * r + 1)**2 - 60 * r - 1) / (15 * r**2)
    sigma = np.zeros_like(e)
    zona1 = abs_e <= ey
    sigma[zona1] = Es * e[zona1]
    zona2 = (abs_e > ey) & (abs_e <= esh)
    sigma[zona2] = fy * np.sign(e[zona2])
    zona3 = (abs_e > esh) & (abs_e <= esu)
    delta_e = abs_e[zona3] - esh
    parte1 = (m * delta_e + 2) / (60 * delta_e + 2)
    parte2 = delta_e * (60 - m) / (2 * (30 * r + 1)**2)
    sigma[zona3] = np.sign(e[zona3]) * fy * (parte1 + parte2)
    return sigma

def hormigon_mander_no_confinado(e, fc0, ec0, ecu, Ec):
    e = np.asarray(e)
    sigma = np.zeros_like(e)
    Esec = fc0 / ec0
    r = Ec / (Ec - Esec)
    zona1 = (e >= 0) & (e <= ecu)
    x = e[zona1] / ec0
    sigma[zona1] = fc0 * (x * r) / (r - 1 + x ** r)
    return sigma

def resultantes_hormigon(Fibras, sigma_c, tan_theta, c, w, fc0, ec0, ecu, Ec):
    y = Fibras[:, 0]
    a = Fibras[:, 1] * w
    e = tan_theta * (y - c)
    sigma = sigma_c(e, fc0, ec0, ecu, Ec)
    N = np.sum(sigma * a)
    M = np.sum(sigma * a * (y - c))
    return N, M

def resultantes(theta, Fu, w, As, c, fc0, ec0, ecu, fy, fsu, Es, ey, esh, esu, Ec):
    tan_theta = np.tan(theta)
    N_UC, M_UC = resultantes_hormigon(Fu, hormigon_mander_no_confinado, tan_theta, c, w, fc0, ec0, ecu, Ec)
    es = tan_theta * (As[:, 1] - c)
    sigma_s = acero_park(es, fy, fsu, Es, ey, esh, esu)
    N_S = np.sum(sigma_s * As[:, 0])
    M_S = np.sum(sigma_s * As[:, 0] * (As[:, 1] - c))
    return N_UC + N_S, M_UC + M_S

def momrot(theta, Fu, w, As, h, tol, cmin, cmax, fc0, ec0, ecu, fy, fsu, Es, ey, esh, esu, Ec):
    def equilibrio(c):
        N, _ = resultantes(theta, Fu, w, As, c, fc0, ec0, ecu, fy, fsu, Es, ey, esh, esu, Ec)
        return N
    c = brentq(equilibrio, cmin, cmax, xtol=tol)
    _, M = resultantes(theta, Fu, w, As, c, fc0, ec0, ecu, fy, fsu, Es, ey, esh, esu, Ec)
    return M, c

def diagrama_MC(Fu, w, As, h, tol, thetaf, m, fc0, ec0, ecu, fy, fsu, Es, ey, esh, esu, Ec):
    dtheta = thetaf / m
    thetas = np.linspace(0, thetaf - dtheta, m)
    M = np.zeros(m)
    c_sol = np.zeros(m)
    delta_frac = 0.01
    cmin_base = 0
    cmax_base = h
    M[0], c_sol[0] = momrot(thetas[0], Fu, w, As, h, tol, cmin_base, cmax_base,
                            fc0, ec0, ecu, fy, fsu, Es, ey, esh, esu, Ec)
    for i in range(1, m):
        delta = h * delta_frac
        cmin = max(c_sol[i-1] - delta, cmin_base)
        cmax = min(c_sol[i-1] + delta, cmax_base)
        try:
            M[i], c_sol[i] = momrot(thetas[i], Fu, w, As, h, tol, cmin, cmax,
                                    fc0, ec0, ecu, fy, fsu, Es, ey, esh, esu, Ec)
        except ValueError:
            M[i], c_sol[i] = momrot(thetas[i], Fu, w, As, h, tol, cmin_base, cmax_base,
                                    fc0, ec0, ecu, fy, fsu, Es, ey, esh, esu, Ec)
    return M, thetas

def ejecutar_mc_mander_no_confinado_viga (datos_hormigon, datos_acero, datos_seccion, datos_fibras):
    fc0 = float(datos_hormigon.get("esfuerzo_fc"))              # Esfuerzo máximo (kg/cm² o MPa)
    Ec = float(datos_hormigon.get("modulo_Ec"))
    Es = float(datos_acero.get("modulo_Es"))                 # Módulo de elasticidad (kg/cm² o MPa)
    ec0 = float(datos_hormigon.get("def_max_sin_confinar"))     # Deformación máxima (pico)
    ecu = float(datos_hormigon.get("def_ultima_sin_confinar")) 
    esu = float(datos_hormigon.get("def_ultima_confinada"))     # Deformación última
    fy = float(datos_acero.get("esfuerzo_fy"))     # Esfuerzo de fluencia
    fsu = float(datos_acero.get("esfuerzo_ultimo_acero"))
    ey = float(datos_acero.get("def_fluencia_acero"))
    esh = float(datos_acero.get("def_inicio_endurecimiento"))
    b = float(datos_seccion.get("disenar_viga_base"))     # Esfuerzo de fluencia
    h = float(datos_seccion.get("disenar_viga_altura"))     # Esfuerzo de fluencia
    rec = float(datos_seccion.get("disenar_viga_recubrimiento"))     # Esfuerzo de fluencia
    nx = int(float(datos_fibras.get("fibras_x")))
    ny = int(float(datos_fibras.get("fibras_y")))
    n_inf = int(float(datos_seccion.get("disenar_viga_varillas_inferior")))
    n_sup = int(float(datos_seccion.get("disenar_viga_varillas_superior")))
    tol = 1e-3
    thetaf = 4/1000
    m = 100
    de = float(datos_seccion.get("disenar_viga_diametro_transversal"))/10     # Esfuerzo de fluencia
    d_inf = float(datos_seccion.get("disenar_viga_diametro_inferior"))/10
    d_sup = float(datos_seccion.get("disenar_viga_diametro_superior"))/10
    As = barras_areaXY(b, h, rec, de, n_inf, n_sup, d_inf, d_sup)
    Fu, w = malla(h, b, nx, ny)
    M, thetas = diagrama_MC(Fu, w, As, h, tol, thetaf, m,
                               fc0, ec0, ecu, fy, fsu, Es, ey, esh, esu, Ec)
    return M/10**5, thetas*100

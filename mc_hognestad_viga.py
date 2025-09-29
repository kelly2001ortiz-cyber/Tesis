import numpy as np
from scipy.optimize import brentq

def barras(b, h, r, de, n_inf, n_sup, d_inf, d_sup):
    rec = r + de
    As = []
    # capa inferior
    area_inf = n_inf * (np.pi * (d_inf ** 2) / 4)
    y_inf = rec + d_inf / 2
    As.append([area_inf, y_inf])
    # capa superior
    area_sup = n_sup * (np.pi * (d_sup ** 2) / 4)
    y_sup = h - rec - d_sup / 2
    As.append([area_sup, y_sup])
    return np.array(As, dtype=float)

def malla(b, h, r, de, n):
    rec = r + de / 2
    y_edges = np.linspace(0, h, n + 1)
    add = []
    if 0 < rec < h: add.append(rec)
    if 0 < h - rec < h: add.append(h - rec)
    if add:
        y_edges = np.unique(np.concatenate([y_edges, np.array(add)]))
        y_edges.sort()
    y  = (y_edges[:-1] + y_edges[1:]) / 2
    dy = np.diff(y_edges)
    A_cover = dy * b
    Fcover = np.column_stack((y, A_cover))
    return Fcover

def acero_park(es, fy, fsu, Es, ey, esh, esu):
    es = np.asarray(es)
    abs_es = np.abs(es)
    r = esu - esh
    m = ((fsu / fy) * (30 * r + 1)**2 - 60 * r - 1) / (15 * r**2)
    fs = np.zeros_like(es)
    z1 = (abs_es <= ey)
    fs[z1] = Es * es[z1]
    z2 = (abs_es > ey) & (abs_es <= esh)
    fs[z2] = fy * np.sign(es[z2])
    z3 = (abs_es > esh) & (abs_es <= esu)
    delta_e = abs_es[z3] - esh
    parte1 = (m * delta_e + 2) / (60 * delta_e + 2)
    parte2 = delta_e * (60 - m) / (2 * (30 * r + 1)**2)
    fs[z3] = np.sign(es[z3]) * fy * (parte1 + parte2)
    return fs

def hognestad(ec, fc0, ec0, esp):
    e = np.asarray(ec)
    fc = np.zeros_like(ec)
    z1 = (ec >= 0) & (ec <= ec0)
    fc[z1] = fc0 * (2 * (ec[z1] / ec0) - (ec[z1] / ec0) ** 2)
    z2 = (ec > ec0) & (ec <= esp)
    fc[z2] = fc0 * (1 - 0.15 * (ec[z2] - ec0) / (esp - ec0))
    return fc

def resultantes_hormigon(Fibras, sigma_c, tan_theta, c, fc0, ec0, ecu):
    y = Fibras[:, 0]
    a = Fibras[:, 1]
    ec = tan_theta * (y - c)
    sigma = sigma_c(ec, fc0, ec0, ecu)
    N = np.sum(sigma * a)
    M = np.sum(sigma * a * (y - c))
    return N, M

def resultantes(theta, Fu, As, c, fc0, ec0, ecu, fy, fsu, Es, ey, esh, esu):
    tan_theta = np.tan(theta)
    N_UC, M_UC = resultantes_hormigon(Fu, hognestad, tan_theta, c, fc0, ec0, ecu)
    es = tan_theta * (As[:, 1] - c)
    sigma_s = acero_park(es, fy, fsu, Es, ey, esh, esu)
    N_S = np.sum(sigma_s * As[:, 0])
    M_S = np.sum(sigma_s * As[:, 0] * (As[:, 1] - c))
    return N_UC + N_S, M_UC + M_S

def momrot(theta, Fu, As, h, tol, cmin, cmax, fc0, ec0, ecu, fy, fsu, Es, ey, esh, esu):
    def equilibrio(c):
        N, _ = resultantes(theta, Fu, As, c, fc0, ec0, ecu, fy, fsu, Es, ey, esh, esu)
        return N
    c = brentq(equilibrio, cmin, cmax, xtol=tol)
    _, M = resultantes(theta, Fu, As, c, fc0, ec0, ecu, fy, fsu, Es, ey, esh, esu)
    return M, c

def diagrama_MC(Fu, As, h, tol, thetaf, m, fc0, ec0, ecu, fy, fsu, Es, ey, esh, esu):
    dtheta = thetaf / m
    thetas = np.linspace(0, thetaf - dtheta, m)
    M = np.zeros(m)
    c_sol = np.zeros(m)
    delta_frac = 0.01
    cmin_base = 0
    cmax_base = h
    M[0], c_sol[0] = momrot(thetas[0], Fu, As, h, tol, cmin_base, cmax_base,
                            fc0, ec0, ecu, fy, fsu, Es, ey, esh, esu)
    for i in range(1, m):
        delta = h * delta_frac
        cmin = max(c_sol[i-1] - delta, cmin_base)
        cmax = min(c_sol[i-1] + delta, cmax_base)
        try:
            M[i], c_sol[i] = momrot(thetas[i], Fu, As, h, tol, cmin, cmax,
                                    fc0, ec0, ecu, fy, fsu, Es, ey, esh, esu)
        except ValueError:
            M[i], c_sol[i] = momrot(thetas[i], Fu, As, h, tol, cmin_base, cmax_base,
                                    fc0, ec0, ecu, fy, fsu, Es, ey, esh, esu)
    return M, thetas

def ejecutar_mc_hognestad_viga (datos_hormigon, datos_acero, datos_seccion, datos_fibras):
    fc0 = float(datos_hormigon.get("esfuerzo_fc"))
    ec0 = float(datos_hormigon.get("def_max_sin_confinar"))
    esp = float(datos_hormigon.get("def_ultima_sin_confinar"))

    Es = float(datos_acero.get("modulo_Es"))
    fy = float(datos_acero.get("esfuerzo_fy"))
    fsu = float(datos_acero.get("esfuerzo_ultimo_acero"))
    ey = float(datos_acero.get("def_fluencia_acero"))
    esh = float(datos_acero.get("def_inicio_endurecimiento"))
    esu = float(datos_hormigon.get("def_ultima_confinada"))

    b = float(datos_seccion.get("disenar_viga_base"))
    h = float(datos_seccion.get("disenar_viga_altura"))
    r = float(datos_seccion.get("disenar_viga_recubrimiento"))
    n_inf = int(float(datos_seccion.get("disenar_viga_varillas_inferior")))
    n_sup = int(float(datos_seccion.get("disenar_viga_varillas_superior")))
    de = float(datos_seccion.get("disenar_viga_diametro_transversal"))/10
    d_inf = float(datos_seccion.get("disenar_viga_diametro_inferior"))/10
    d_sup = float(datos_seccion.get("disenar_viga_diametro_superior"))/10
    
    nx = int(float(datos_fibras.get("fibras_x")))
    ny = int(float(datos_fibras.get("fibras_y")))

    tol = 1e-3
    thetaf = 4/1000
    m = 100

    As = barras(b, h, r, de, n_inf, n_sup, d_inf, d_sup)
    Fu = malla(b, h, r, de, ny)
    M, thetas = diagrama_MC(Fu, As, h, tol, thetaf, m,
                               fc0, ec0, esp, fy, fsu, Es, ey, esh, esu)
    return M/10**5, thetas*100

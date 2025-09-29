import numpy as np
from scipy.optimize import brentq
from scipy.integrate import simpson

def barras_columna(h, r, dest, n_x, n_y, d_corner, d_edge):
    As_edge = 0.25 * np.pi * d_edge**2
    As_corner = 0.25 * np.pi * d_corner**2
    y_inf_edge = r + dest + d_edge/2
    y_sup_edge = h - y_inf_edge
    y_inf_corner = r + dest + d_corner/2
    y_sup_corner = h - y_inf_corner
    y_edge = np.linspace(y_inf_corner, y_sup_corner, n_y)[1:-1]
    y = np.concatenate(([y_inf_corner],[y_inf_edge], y_edge, [y_sup_edge], [y_sup_corner]))
    nbarras = np.full(n_y + 2, 2, dtype=int)
    nbarras[1]  = (n_x - 2)
    nbarras[n_y] = (n_x - 2)
    areas = nbarras * As_edge
    areas[0] = 2 * As_corner
    areas[-1] = 2 * As_corner
    As = np.column_stack([areas, y])
    return As

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
    core_width = max(b - 2 * rec, 0)
    y_in_core  = (y >= rec) & (y <= (h - rec))
    A_core  = dy * core_width * y_in_core.astype(float)
    A_cover = dy * b - A_core
    Fcover = np.column_stack((y, A_cover))
    Fcore = np.column_stack((y[y_in_core], A_core[y_in_core]))
    return Fcover, Fcore

def park(es, fy, fsu, Es, ey, esh, esu):
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

def mander_u(ec, fc0, ec0, esp, Ec, _):
    ec = np.asarray(ec)
    fc = np.zeros_like(ec)
    ec00 = 2 * ec0
    Esec = fc0 / ec0
    r = Ec / (Ec - Esec)
    zona1 = (ec >= 0) & (ec <= esp)
    x = ec[zona1] / ec0
    fc[zona1] = fc0 * (x * r) / (r - 1 + x ** r)
    z2 = (ec > ec00) & (ec <= esp)
    fc[z2] = fc0 * (2 * r) / (r - 1 + 2 ** r) * (1 - (ec[z2] - ec00) / (esp - ec00))
    return fc

def mander_c(ec, fc0, ec0, _, Ec, datos):
    h, b, r, fy, Sc, de, d_corner, d_edge, Nb, NLx, NLy, ecu = datos

    # calculo de f'cc - Mander, J. B., Priestley, M. J. N., and Park, R. (1984) "Seismic design of bridge piers"
    def fccfco(flx, fly, fc0):
        sigma1, sigma2, sigma3 = -min(flx, fly), -max(flx, fly), -fc0
        tau_oct_i, tau_oct_j = 1, 2
        tol = 1e-6
        for i in range(1000):
            # esfuerzos octaedricos
            sigma_oct = (sigma1 + sigma2 + sigma3) / 3
            tau_oct_i = (((sigma1 - sigma2) ** 2 + (sigma2 - sigma3) ** 2 + (sigma3 - sigma1) ** 2) ** 0.5 ) / 3
            cos_theta = (sigma1 - sigma_oct) / (2 ** 0.5 * tau_oct_i)
            # coeficiente de esfuerzo normal octaedrico
            sigmap_oct = sigma_oct / fc0
            # ecuaciones de los meridianos
            T = 0.069232 - 0.661091 * sigmap_oct - 0.049350 * sigmap_oct ** 2
            C = 0.122965 - 1.150502 * sigmap_oct - 0.315545 * sigmap_oct ** 2
            # coeficiente de esfuerzo cortante octaedrico
            D = 4 * (C ** 2 - T ** 2) * cos_theta ** 2
            tau_oct_j = fc0 * C * (D / (2 * cos_theta) + (2 * T - C) * (D + 5 * T ** 2 - 4 * T * C) ** 0.5) / (D + (2 * T - C) ** 2)            
            sigma3_nuevo = (sigma1 + sigma2) / 2 - (4.5 * tau_oct_j ** 2 - 0.75 * (sigma1 - sigma2) ** 2) ** 0.5
            if abs(tau_oct_i - tau_oct_j) < tol and abs(sigma3 - sigma3_nuevo) < tol:
                sigma3 = sigma3_nuevo
                break
            sigma3 = sigma3_nuevo
        return -sigma3
    # dimensiones del nucleo
    dc = h - 2 * r - de              # Altura confinada
    bc = b - 2 * r - de              # Base confinada
    Ss = Sc - de                     # Longitud libre entre estribos
    # area inefectiva (zona no confinada)
    Wx = (bc - de - 2 * d_corner - (NLx - 2) * d_edge) / (NLx - 1)
    Wy = (dc - de - 2 * d_corner - (NLy - 2) * d_edge) / (NLy - 1)
    Ainef = (2 * (NLx - 1) * Wx ** 2 / 6) + (2 * (NLy - 1) * Wy ** 2 / 6)
    # Area efectiva confinada
    Ae = (bc * dc - Ainef) * (1 - Ss / (2 * bc)) * (1 - Ss / (2 * dc))
    # cuantia del acero longitudinal
    Ast = np.pi * (d_corner ** 2 + (Nb - 4) * d_edge ** 2 / 4)
    Ac = bc * dc
    Acc = Ac - Ast
    pcc = Ast / Acc
    # coeficiente de confinamiento efectivo
    ke = Ae / Acc
    # presion lateral de confinamiento
    Ash = np.pi * de ** 2 / 4
    px = (NLx * Ash * bc) / (Sc * bc * dc)
    py = (NLy * Ash * dc) / (Sc * bc * dc)
    flx = ke * px * fy
    fly = ke * py * fy
    # incremento de resistencia por confinamiento
    fcc = fccfco(flx, fly, fc0)
    ecc = ec0 * (1 + 5 * (fcc / fc0 - 1))
    # modulo secante y parámetro r
    Esec = fcc / ecc
    r = Ec / (Ec - Esec)
    # cuantia volumetrica de estribos
    psh = (NLx * Ash * bc + NLy * Ash * dc) / (Acc * Sc)
    # diagrama esfuerzo-deformación
    ec = np.asarray(ec)
    zona1 = (ec >= 0) & (ec <= ecu)
    fc = np.zeros_like(ec)
    x = ec[zona1] / ecc
    fc[zona1] = fcc * (x * r) / (r - 1 + x ** r)
    return fc

def resultantes_hormigon(Fibras, sigma_c, tan_theta, c, fc0, ec0, esp, Ec, datos):
    y = Fibras[:, 0]
    a = Fibras[:, 1]
    ec = tan_theta * (y - c)
    sigma = sigma_c(ec, fc0, ec0, esp, Ec, datos)
    N = np.sum(sigma * a)
    M = np.sum(sigma * a * (y - c))
    return N, M

def resultantes(theta, Fu, Fc, As, c, fc0, ec0, esp, fy, fsu, Es, ey, esh, esu, Ec, datos):
    tan_theta = np.tan(theta)
    N_UC, M_UC = resultantes_hormigon(Fu, mander_u, tan_theta, c, fc0, ec0, esp, Ec, datos)
    N_CC, M_CC = resultantes_hormigon(Fc, mander_c, tan_theta, c, fc0, ec0, esp, Ec, datos)
    es = tan_theta * (As[:, 1] - c)
    sigma_s = park(es, fy, fsu, Es, ey, esh, esu)
    N_S = np.sum(sigma_s * As[:, 0])
    M_S = np.sum(sigma_s * As[:, 0] * (As[:, 1] - c))
    return (N_UC + N_CC + N_S), (M_UC + M_CC + M_S)

def momrot(theta, Fu, Fc, As, h, tol, cmin, cmax, fc0, ec0, esp, fy, fsu, Es, ey, esh, esu, Ec, datos):
    def equilibrio(c):
        N, _ = resultantes(theta, Fu, Fc, As, c, fc0, ec0, esp, fy, fsu, Es, ey, esh, esu, Ec, datos)
        return N
    c = brentq(equilibrio, cmin, cmax, xtol=tol)
    _, M = resultantes(theta, Fu, Fc, As, c, fc0, ec0, esp, fy, fsu, Es, ey, esh, esu, Ec, datos)
    return M, c

def diagrama_MC(Fu, Fc, As, h, tol, thetaf, m, fc0, ec0, esp, fy, fsu, Es, ey, esh, esu, Ec, datos):
    dtheta = thetaf / m
    thetas = np.linspace(0, thetaf - dtheta, m)
    M = np.zeros(m)
    c_sol = np.zeros(m)
    delta_frac = 0.01
    cmin_base = 0
    cmax_base = h
    M[0], c_sol[0] = momrot(thetas[0], Fu, Fc, As, h, tol, cmin_base, cmax_base,
                            fc0, ec0, esp, fy, fsu, Es, ey, esh, esu, Ec, datos)
    for i in range(1, m):
        delta = h * delta_frac
        cmin = max(c_sol[i-1] - delta, cmin_base)
        cmax = min(c_sol[i-1] + delta, cmax_base)
        try:
            M[i], c_sol[i] = momrot(thetas[i], Fu, Fc, As, h, tol, cmin, cmax,
                                    fc0, ec0, esp, fy, fsu, Es, ey, esh, esu, Ec, datos)
        except ValueError:
            M[i], c_sol[i] = momrot(thetas[i], Fu, Fc, As, h, tol, cmin_base, cmax_base,
                                    fc0, ec0, esp, fy, fsu, Es, ey, esh, esu, Ec, datos)
    return M, thetas

# -------------------------------------------------------------------------------------- #
def mander_cc(fc0, Ec, ec0, fy, b, h, r, Sc, de, dbe, dbi, Nb, NLx, NLy, ecu):
    # calculo de f'cc - Mander, J. B., Priestley, M. J. N., and Park, R. (1984) "Seismic design of bridge piers"
    def fccfco(flx, fly, fc0):
        sigma1, sigma2, sigma3 = -min(flx, fly), -max(flx, fly), -fc0
        tau_oct_i, tau_oct_j = 1, 2
        tol = 1e-6
        for i in range(1000):
            # esfuerzos octaedricos
            sigma_oct = (sigma1 + sigma2 + sigma3) / 3
            tau_oct_i = (((sigma1 - sigma2) ** 2 + (sigma2 - sigma3) ** 2 + (sigma3 - sigma1) ** 2) ** 0.5 ) / 3
            cos_theta = (sigma1 - sigma_oct) / (2 ** 0.5 * tau_oct_i)
            # coeficiente de esfuerzo normal octaedrico
            sigmap_oct = sigma_oct / fc0
            # ecuaciones de los meridianos
            T = 0.069232 - 0.661091 * sigmap_oct - 0.049350 * sigmap_oct ** 2
            C = 0.122965 - 1.150502 * sigmap_oct - 0.315545 * sigmap_oct ** 2
            # coeficiente de esfuerzo cortante octaedrico
            D = 4 * (C ** 2 - T ** 2) * cos_theta ** 2
            tau_oct_j = fc0 * C * (D / (2 * cos_theta) + (2 * T - C) * (D + 5 * T ** 2 - 4 * T * C) ** 0.5) / (D + (2 * T - C) ** 2)            
            sigma3_nuevo = (sigma1 + sigma2) / 2 - (4.5 * tau_oct_j ** 2 - 0.75 * (sigma1 - sigma2) ** 2) ** 0.5
            if abs(tau_oct_i - tau_oct_j) < tol and abs(sigma3 - sigma3_nuevo) < tol:
                sigma3 = sigma3_nuevo
                break
            sigma3 = sigma3_nuevo
        return -sigma3
    # dimensiones del nucleo
    dc = h - 2 * r - de              # Altura confinada
    bc = b - 2 * r - de              # Base confinada
    Ss = Sc - de                       # Longitud libre entre estribos
    # area inefectiva (zona no confinada)
    Wx = (bc - de - 2 * dbe - (NLx - 2) * dbi) / (NLx - 1)
    Wy = (dc - de - 2 * dbe - (NLy - 2) * dbi) / (NLy - 1)
    Ainef = (2 * (NLx - 1) * Wx ** 2 / 6) + (2 * (NLy - 1) * Wy ** 2 / 6)
    # Area efectiva confinada
    Ae = (bc * dc - Ainef) * (1 - Ss / (2 * bc)) * (1 - Ss / (2 * dc))
    # cuantia del acero longitudinal
    Ast = np.pi * (dbe ** 2 + (Nb - 4) * dbi ** 2 / 4)
    Ac = bc * dc
    Acc = Ac - Ast
    pcc = Ast / Acc
    # coeficiente de confinamiento efectivo
    ke = Ae / Acc
    # presion lateral de confinamiento
    Ash = np.pi * de ** 2 / 4
    px = (NLx * Ash * bc) / (Sc * bc * dc)
    py = (NLy * Ash * dc) / (Sc * bc * dc)
    flx = ke * px * fy
    fly = ke * py * fy
    # incremento de resistencia por confinamiento
    fcc = fccfco(flx, fly, fc0)
    ecc = ec0 * (1 + 5 * (fcc / fc0 - 1))
    # modulo secante y parámetro r
    Esec = fcc / ecc
    r = Ec / (Ec - Esec)
    # cuantia volumetrica de estribos
    psh = (NLx * Ash * bc + NLy * Ash * dc) / (Acc * Sc)
    # diagrama esfuerzo-deformacion
    ec = np.linspace(0, ecu, 100)
    fc = np.zeros_like(ec)
    x = ec / ecc
    fc = fcc * (x * r) / (r - 1 + x ** r)
    return ec, fc, psh, Acc

def mander_uc(fc0, Ec, ec0, esp):
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

def park_sh(fy, fsu, Es, ey, esh, esu):
    es = np.linspace(0, esu, 100)
    fs = np.zeros_like(es)
    # zona elestica
    z1 = (es <= ey)
    fs[z1] = Es * es[z1]
    # zona perfectamente plastica
    z2 = (es > ey) & (es <= esh)
    fs[z2] = fy
    # zona de endurecimiento por deformacion
    z3 = (es > esh) & (es <= esu)
    r = esu - esh
    m = ((fsu / fy) * (30 * r + 1) ** 2 - 60 * r - 1) / (15 * r ** 2)  
    delta_e = es[z3] - esh
    parte1 = (m * delta_e + 2) / (60 * delta_e + 2)
    parte2 = delta_e * (60 - m) / (2 * (30 * r + 1) ** 2)
    fs[z3] = np.sign(es[z3]) * fy * (parte1 + parte2)
    return es, fs

def ejecutar_mc_mander_confinado_columnaY (datos_hormigon, datos_acero, datos_seccion, datos_fibras):
    fc0 = float(datos_hormigon.get("esfuerzo_fc"))
    Ec = float(datos_hormigon.get("modulo_Ec"))
    ec0 = float(datos_hormigon.get("def_max_sin_confinar"))
    esp = float(datos_hormigon.get("def_ultima_sin_confinar"))

    Es = float(datos_acero.get("modulo_Es"))
    fy = float(datos_acero.get("esfuerzo_fy"))
    fsu = float(datos_acero.get("esfuerzo_ultimo_acero"))
    ey = float(datos_acero.get("def_fluencia_acero"))
    esh = float(datos_acero.get("def_inicio_endurecimiento"))
    esu = float(datos_hormigon.get("def_ultima_confinada"))

    b = float(datos_seccion.get("disenar_columna_base"))
    h = float(datos_seccion.get("disenar_columna_altura"))
    r = float(datos_seccion.get("disenar_columna_recubrimiento"))
    Sc = float(datos_seccion.get("disenar_columna_espaciamiento"))
    de = float(datos_seccion.get("disenar_columna_diametro_transversal"))/10
    d_edge = int(float(datos_seccion.get("disenar_columna_diametro_longitudinal_2")))/10
    d_corner = int(float(datos_seccion.get("disenar_columna_diametro_longitudinal_esq")))/10
    Nb1 = int(float(datos_seccion.get("disenar_columna_varillasX_2")))
    Nb2 = int(float(datos_seccion.get("disenar_columna_varillasY_2")))
    NLx = int(float(datos_seccion.get("disenar_columna_ramalesX")))
    NLy = int(float(datos_seccion.get("disenar_columna_ramalesY")))
    Nb = (Nb1 - 2) * 2 + Nb2 * 2
    
    nx = int(float(datos_fibras.get("fibras_x")))
    ny = int(float(datos_fibras.get("fibras_y")))

    tol = 1e-3
    thetaf = 4/1000
    m = 100

    def g(ecu):
        # hormigon no confinado
        ec_uc, fc_uc = mander_uc(fc0, Ec, ec0, esp)
        A_uc = simpson(fc_uc, ec_uc)
        # acero transversal
        es_sh, fs_sh = park_sh(fy, fsu, Es, ey, esh, esu)
        A_sh = simpson(fs_sh, es_sh)
        # hormigon confinado hasta ecu
        ec_cc, fc_cc, psh, Acc = mander_cc(fc0, Ec, ec0, fy, b, h, r, Sc, de, d_corner, d_edge, Nb, NLx, NLy, ecu)
        A_cc = simpson(fc_cc, ec_cc)
        # balance de energia
        Ush = psh * Acc * A_sh
        Uco = Acc * A_uc
        Ucc = Acc * A_cc
        return Ucc - Uco - Ush
    
    ecu = brentq(g, 0.002, 0.100)
    As = barras_columna(h, r, de, Nb1, Nb2, d_corner, d_edge)
    Fu, Fc = malla(b, h, r, de, ny)
    datos = (h, b, r, fy, Sc, de, d_corner, d_edge, Nb, NLx, NLy, ecu)
    M, thetas = diagrama_MC(Fu, Fc, As, h, tol, thetaf, m,
                               fc0, ec0, esp, fy, fsu, Es, ey, esh, esu, Ec, datos)
    return M/10**5, thetas*100
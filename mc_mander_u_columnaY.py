import numpy as np
from scipy.optimize import root_scalar

# Coordenadas de barras de acero
def barras_columna(h, r, de, n_x, n_y, d_corner, d_edge):
    As_edge = np.pi * d_edge**2 / 4
    As_corner = np.pi * d_corner**2 / 4
    y_inf_edge = r + de + d_edge / 2
    y_sup_edge = h - y_inf_edge
    y_inf_corner = r + de + d_corner / 2
    y_sup_corner = h - y_inf_corner
    y_edge = np.linspace(y_inf_corner, y_sup_corner, n_y)[1:-1]
    yi = np.concatenate(([y_inf_corner],[y_inf_edge], y_edge, [y_sup_edge], [y_sup_corner]))
    yi =  h / 2 - yi
    nbarras = np.full(n_y + 2, 2, dtype=int)
    nbarras[1]  = n_x - 2
    nbarras[-2] = n_x - 2
    Ai = nbarras * As_edge
    Ai[0] = 2 * As_corner
    Ai[-1] = 2 * As_corner
    As = np.column_stack([yi, Ai])
    return As

# Coordenadas de fibras
def malla(b, h, r, de, n):
    rec = r + de / 2
    y_edges = np.linspace(0, h, n + 1)
    add = []
    if 0 < rec < h: add.append(rec)
    if 0 < h - rec < h: add.append(h - rec)
    if add:
        y_edges = np.unique(np.concatenate([y_edges, np.array(add)]))
    yi  = h / 2 - (y_edges[:-1] + y_edges[1:]) / 2
    dy = np.diff(y_edges)
    Ai_cover = dy * b
    cover = np.column_stack((yi, Ai_cover))
    return cover

# Modelo de Park para acero longitudinal
def park(es, fy, fsu, Es, ey, esh, esu):
    es = np.asarray(es, dtype=float)
    fs = np.zeros_like(es, dtype=float)
    abs_es = np.abs(es)
    sign = np.sign(es)
    # rama elestica lineal
    z1 = (abs_es <= ey)
    fs[z1] = Es * es[z1]
    # rama perfectamente plastica
    z2 = (abs_es > ey) & (abs_es <= esh)
    fs[z2] = fy * sign[z2]
    # rama de endurecimiento por deformacion
    z3 = (abs_es > esh) & (abs_es <= esu)
    delta_e = abs_es[z3] - esh
    r = esu - esh
    m = ((fsu / fy) * (30 * r + 1) ** 2 - 60 * r - 1) / (15 * r ** 2)
    parte1 = (m * delta_e + 2) / (60 * delta_e + 2)
    parte2 = delta_e * (60 - m) / (2 * (30 * r + 1) ** 2)
    fs[z3] = sign[z3] * fy * (parte1 + parte2)
    return fs

# Modelo de Mander para hormigon no confinado
def mander_u(ec, fc0, ec0, esp, Ec):
    ec = np.asarray(ec, dtype=float)
    fc = np.zeros_like(ec, dtype=float)
    ec00 = 2 * ec0
    # modulo secante y parámetro r
    Esec = fc0 / ec0
    r = Ec / (Ec - Esec)
    # rama ascendente curva
    z1 = (ec <= 0) & (ec >= -ec00)
    x = ec[z1] / -ec0
    fc[z1] = -fc0 * (x * r) / (r - 1 + x ** r)
    # rama descendente lineal
    z2 = (ec >= -esp) & (ec < -ec00)
    fc[z2] = -fc0 * (2 * r) / (r - 1 + 2 ** r) * (esp + ec[z2]) / (esp - ec00)
    return fc

# Resultantes del hormigon
def resultantes_hormigon(Fibras, sigma_c, c, phi, fc0, ec0, esp, Ec):
    yi = Fibras[:, 0]
    Ai = Fibras[:, 1]
    ec = -phi * (yi - c)
    sigma = sigma_c(ec, fc0, ec0, esp, Ec)
    N = np.sum(sigma * Ai)
    M = np.sum(sigma * Ai * yi)
    return N, M, ec

# Resultandes del acero
def resultantes_acero(As, sigma_s, c, phi, fy, fsu, Es, ey, esh, esu):
    yi = As[:, 0]
    Ai = As[:, 1]
    es = -phi * (yi - c)
    sigma = sigma_s(es, fy, fsu, Es, ey, esh, esu)
    N = np.sum(sigma * Ai)
    M = np.sum(sigma * Ai * yi)
    return N, M, es

# Suma de resultantes de los materiales
def resultantes(c, phi, Fu, As, fc0, ec0, esp, fy, fsu, Es, ey, esh, esu, Ec, P):
    N_uc, M_uc, e_uc = resultantes_hormigon(Fu, mander_u, c, phi, fc0, ec0, esp, Ec)
    N_s, M_s, e_s = resultantes_acero(As, park, c, phi, fy, fsu, Es, ey, esh, esu)
    N_total = N_uc + N_s - P
    M_total = M_uc + M_s
    return N_total, M_total

# Funcion para encontrar la distancia al eje neutro
def momrot(c_min, c_max, phi, Fu, As, tol, fc0, ec0, esp,
           fy, fsu, Es, ey, esh, esu, Ec, P, h, c_prev, phi_prev):

    def N_equilibrio(c):
        N = resultantes(c, phi, Fu, As, fc0, ec0, esp, fy, fsu, Es, ey, esh, esu, Ec, P)[0]
        return N

    def es_max(c, phi):
        _, _, e_s = resultantes_acero(As, park, c, phi, fy, fsu, Es, ey, esh, esu)
        es_validas = e_s[abs(e_s) < esu]
        es = np.max(abs(es_validas)) if len(es_validas) else -np.inf
        return es
    
    def filtro(roots, es_prev):
        raices = []
        for c in roots:
            es = es_max(c, phi)
            if es >= 0.90*es_prev:
                raices.append(c)
        return raices

    def encontrar_raices(a, b, npts):
        c_vals = np.linspace(a, b, npts)
        N_vals = np.array([N_equilibrio(c) for c in c_vals])
        roots = []
        for c1, c2, N1, N2 in zip(c_vals[:-1], c_vals[1:], N_vals[:-1], N_vals[1:]):
            if abs(N1) < tol:
                roots.append(c1)
            elif N1 * N2 < 0:
                try:
                    sol = root_scalar(N_equilibrio, bracket=[c1, c2], method='brentq')
                    if sol.converged and abs(N_equilibrio(sol.root)) <= tol:
                        roots.append(sol.root)
                except ValueError:
                    pass
        return sorted(roots)

    def buscar_c():
        if c_prev is None:
            return encontrar_raices(c_min, c_max, npts=100)
        ventanas = [0.04*h, 0.08*h, 0.10*h, 0.15*h, 0.25*h, 0.35*h]
        for dc in ventanas:
            a = max(c_min, c_prev - dc)
            b = min(c_max, c_prev + dc)
            roots = encontrar_raices(a, b, npts=25)
            es_prev = es_max(c_prev, phi_prev)
            root = filtro(roots, es_prev)
            if root:
                return root
        return encontrar_raices(c_min, c_max, npts=120)
    
    c_posibles = buscar_c()
    if not c_posibles:
        return None, None

    c = c_posibles[0] if c_prev is None else min(c_posibles, key=lambda x: abs(x - c_prev))
    M = resultantes(c, phi, Fu, As, fc0, ec0, esp, fy, fsu, Es, ey, esh, esu, Ec, P)[1]
    return M, c

# Funcion para obtener el doagrama momento curvatura
def diagrama_MC(Fu, As, h, tol, fc0, ec0, esp, fy, fsu, Es, ey, esh, esu, Ec, P):
    dphi_min, dphi_max = 2e-8, 5e-5
    phi_ini, dphi_ini = 2e-5, 1e-6
    phi_vals = [0.0]
    M_vals = [0.0]
    c_vals = [0.0]

    phi = phi_ini
    dphi = dphi_ini
    c_min = -h/2
    c_max = h/2
    c_prev = None
    phi_prev = None
    Mmax = 0.0
    post_pico = False
    pts_extra = None
    n_pts_extra = 4

    for _ in range(1000):
        Mi, ci = momrot(c_min, c_max, phi, Fu, As, tol, fc0, ec0, esp, fy, fsu, Es, ey, esh, esu, Ec,
                        P, h, c_prev, phi_prev)

        # no hay solución de equilibrio: falla numérica/física
        # si falla, probar reduciendo paso antes de salir
        if Mi is None:
            if dphi > dphi_min:
                dphi = max(0.8*dphi, dphi_min)
                phi += dphi
                continue
            break

        Mi = -Mi

        # guardar resultados
        phi_vals.append(phi)
        M_vals.append(Mi)
        c_vals.append(ci)
        
        # actualizar momento maximo
        if Mi > Mmax:
            Mmax = Mi
        elif Mi < 0.95*Mmax:
            post_pico = True

        # control post-pico
        if post_pico and Mi < 0.7*Mmax:
            dphi = max(0.8*dphi, dphi_min)
            if pts_extra is None:
                pts_extra = n_pts_extra
            pts_extra -= 1
            if pts_extra < 0:
                break
            
        # adaptacion del paso
        if len(M_vals) >= 2:
            dM = abs(M_vals[-1] - M_vals[-2]) / max(abs(Mmax), 1e-6)
            if dM > 0.05:
                dphi = max(0.5*dphi, dphi_min)
            elif dM < 0.01:
                dphi = min(1.2*dphi, dphi_max)

        c_prev = ci
        phi_prev = phi
        phi += dphi
    return np.array(M_vals, dtype=float), np.array(phi_vals, dtype=float)

def ejecutar_mc_mander_no_confinado_columnaY (datos_hormigon, datos_acero, datos_seccion, datos_fibras):
    fc0 = float(datos_hormigon.get("esfuerzo_fc"))
    Ec = float(datos_hormigon.get("modulo_Ec"))
    ec0 = float(datos_hormigon.get("def_max_sin_confinar"))
    esp = float(datos_hormigon.get("def_ultima_sin_confinar")) 

    Es = float(datos_acero.get("modulo_Es"))
    fy = float(datos_acero.get("esfuerzo_fy"))
    ey = float(datos_acero.get("def_fluencia_acero"))
    fsu = float(datos_acero.get("esfuerzo_ultimo_acero"))
    esh = float(datos_acero.get("def_inicio_endurecimiento"))
    esu = float(datos_acero.get("def_ultima_acero"))

    b = float(datos_seccion.get("disenar_columna_base"))
    h = float(datos_seccion.get("disenar_columna_altura"))
    r = float(datos_seccion.get("disenar_columna_recubrimiento"))
    Nb1 = int(float(datos_seccion.get("disenar_columna_varillasX_2")))
    Nb2 = int(float(datos_seccion.get("disenar_columna_varillasY_2")))
    de = float(datos_seccion.get("disenar_columna_diametro_transversal"))/10
    d_edge = int(float(datos_seccion.get("disenar_columna_diametro_longitudinal_2")))/10
    d_corner = int(float(datos_seccion.get("disenar_columna_diametro_longitudinal_esq")))/10
    P = float(datos_seccion.get("disenar_columna_axial"))

    nx = int(float(datos_fibras.get("fibras_x")))
    ny = int(float(datos_fibras.get("fibras_y")))

    tol = 1e-5
    
    As = barras_columna(h, r, de, Nb1, Nb2, d_corner, d_edge)
    Fu = malla(b, h, r, de, ny)
    M, phi = diagrama_MC(Fu, As, h, tol, fc0, ec0, esp, fy, fsu, Es, ey, esh, esu, Ec, P)
    
    return M/10**5, phi*100

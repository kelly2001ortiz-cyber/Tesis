import numpy as np
from scipy.optimize import root_scalar
from materiales import modelos
from seccion import utilidades

park = modelos.park
hognestad = modelos.hognestad
mander_u = modelos.mander_u
mander_c = modelos.mander_c
buscar_ecu = modelos.buscar_ecu

barras_columna = utilidades.barras_columna
barras_viga = utilidades.barras_viga
malla = utilidades.malla

def sigma_hormigon(nombre_modelo):
    nombre = nombre_modelo.lower().strip()
    modelos_h = {
        "hognestad": hognestad,
        "mander_u": mander_u,
        "mander_c": mander_c,
    }
    return modelos_h[nombre]

# Resultantes del hormigon
def resultantes_hormigon(fibras, sigma_c, c, phi, fc0, ec0, esp, Ec, datos_h):
    yi = fibras[:, 0]
    Ai = fibras[:, 1]
    ec = -phi * (yi - c)
    sigma = sigma_c(ec, fc0, ec0, esp, Ec, datos_h, 1)
    N = np.sum(sigma * Ai)
    M = np.sum(sigma * Ai * yi)
    return N, M

# Resultantes del acero
def resultantes_acero(As, sigma_s, c, phi, fy, fsu, Es, ey, esh, esu):
    yi = As[:, 0]
    Ai = As[:, 1]
    es = -phi * (yi - c)
    sigma = sigma_s(es, fy, fsu, Es, ey, esh, esu)
    N = np.sum(sigma * Ai)
    M = np.sum(sigma * Ai * yi)
    return N, M

# Suma de resultantes de los materiales
def resultantes(c, phi, cover, core, As, fc0, ec0, esp, Ec, fy, fsu, Es, ey, esh, esu, P, datos_h, sg_cover, sg_core):
    N_uc, M_uc = resultantes_hormigon(cover, sg_cover, c, phi, fc0, ec0, esp, Ec, datos_h)
    N_cc, M_cc = resultantes_hormigon(core, sg_core, c, phi, fc0, ec0, esp, Ec, datos_h)
    N_s, M_s = resultantes_acero(As, park, c, phi, fy, fsu, Es, ey, esh, esu)

    N_total = N_uc + N_cc + N_s - P
    M_total = M_uc + M_cc + M_s
    return N_total, M_total

# Funcion para encontrar la distancia al eje neutro
def momrot(c_min, c_max, phi, cover, core, As, tol, h, fc0, ec0, esp, Ec,
           fy, fsu, Es, ey, esh, esu, P, datos_h, sg_cover, sg_core, c_prev=None, phi_prev=None):

    def N_equilibrio(c):
        N = resultantes(c, phi, cover, core, As, fc0, ec0, esp, Ec,
                        fy, fsu, Es, ey, esh, esu, P, datos_h, sg_cover, sg_core)[0]
        return N

    def es_max(c_eval, phi_eval):
        yi = As[:, 0]
        e_s = -phi_eval * (yi - c_eval)
        es_validas = e_s[np.abs(e_s) < esu]
        es = np.max(abs(es_validas)) if len(es_validas) else -np.inf
        return es

    def filtro(roots, es_prev):
        raices = []
        for c_root in roots:
            es = es_max(c_root, phi)
            if es >= 0.90 * es_prev:
                raices.append(c_root)
        return raices

    def encontrar_raices(a, b, npts):
        c_vals = np.linspace(a, b, npts)
        N_vals = np.fromiter((N_equilibrio(c) for c in c_vals), dtype=float, count=npts)
        roots = []
        
        idx_signo = np.flatnonzero(N_vals[:-1] * N_vals[1:] < 0.0)
        idx_cero = np.flatnonzero(np.abs(N_vals[:-1]) < tol)
        idxs = np.unique(np.concatenate((idx_cero, idx_signo)))

        for i in idxs:
            c1 = c_vals[i]
            c2 = c_vals[i + 1]
            N1 = N_vals[i]
            N2 = N_vals[i + 1]

            if abs(N1) < tol:
                roots.append(c1)
            elif N1 * N2 < 0.0:
                try:
                    sol = root_scalar(N_equilibrio, bracket=[c1, c2], method="brentq")
                    if sol.converged and abs(N_equilibrio(sol.root)) <= tol:
                        roots.append(sol.root)
                except ValueError:
                    pass
        if not roots:
            return []
        return np.unique(np.array(roots, dtype=float)).tolist()

    def buscar_c():
        # Primer punto
        if c_prev is None:
            return encontrar_raices(c_min, c_max, npts=50)

        es_prev = es_max(c_prev, phi_prev)

        # Intento de busqueda directo cerca de la raíz previa
        dc0 = 0.02*h
        a0 = max(c_min, c_prev - dc0)
        b0 = min(c_max, c_prev + dc0)

        N_a0 = N_equilibrio(a0)
        N_b0 = N_equilibrio(b0)

        if abs(N_a0) < tol:
            roots = filtro([a0], es_prev)
            if roots:
                return roots

        if abs(N_b0) < tol:
            roots = filtro([b0], es_prev)
            if roots:
                return roots

        if N_a0 * N_b0 < 0.0:
            try:
                sol = root_scalar(N_equilibrio, bracket=[a0, b0], method="brentq")
                if sol.converged and abs(N_equilibrio(sol.root)) <= tol:
                    roots = filtro([sol.root], es_prev)
                    if roots:
                        return roots
            except ValueError:
                pass

        # Si falla el intento directo, usar ventanas crecientes
        ventanas = [0.04*h, 0.08*h, 0.10*h, 0.15*h, 0.25*h, 0.35*h]

        for dc in ventanas:
            a = max(c_min, c_prev - dc)
            b = min(c_max, c_prev + dc)
            roots = encontrar_raices(a, b, npts=10)
            root = filtro(roots, es_prev)
            if root:
                return root
        
        return encontrar_raices(c_min, c_max, npts=50)

    c_posibles = buscar_c()
    if not c_posibles:
        return None, None

    c = c_posibles[0] if c_prev is None else min(c_posibles, key=lambda x: abs(x - c_prev))
    M = resultantes(c, phi, cover, core, As, fc0, ec0, esp, Ec, fy, fsu, Es, ey, esh, esu, P, datos_h, sg_cover, sg_core)[1]
    return M, c

# Funcion para obtener el diagrama momento-curvatura
def diagrama_MC(cover, core, As, tol, h, fc0, ec0, esp, Ec, fy, fsu, Es, ey, esh, esu, P, datos_h, sg_cover, sg_core):
    
    dphi_min, dphi_max = 2e-8, 5e-5
    phi_ini, dphi_ini = 2e-5, 1e-6

    phi_vals = [0.0]
    M_vals = [0.0]
    c_vals = [0.0]

    phi = phi_ini
    dphi = dphi_ini
    c_min = -h / 2
    c_max = h / 2
    c_prev = None
    phi_prev = None
    Mmax = 0.0
    post_pico = False
    pts_extra = None
    n_pts_extra = 4

    for _ in range(1000):
        Mi, ci = momrot(c_min, c_max, phi, cover, core, As, tol, h, fc0, ec0, esp, Ec,
                        fy, fsu, Es, ey, esh, esu, P, datos_h, sg_cover, sg_core, c_prev, phi_prev)

        # No hay solucion de equilibrio: falla numerica/fisica.
        # Si falla, probar reduciendo paso antes de salir.
        if Mi is None:
            if dphi > dphi_min:
                dphi = max(0.80 * dphi, dphi_min)
                continue
            break

        Mi = -Mi

        # Guardar resultados
        phi_vals.append(phi)
        M_vals.append(Mi)
        c_vals.append(ci)

        # Actualizar momento maximo
        if Mi > Mmax:
            Mmax = Mi
        elif Mi < 0.90 * Mmax:
            post_pico = True

        # Control post-pico
        if post_pico and Mi < 0.70 * Mmax:
            dphi = max(0.80 * dphi, dphi_min)
            if pts_extra is None:
                pts_extra = n_pts_extra
            pts_extra -= 1
            if pts_extra < 0:
                break

        # Adaptacion del paso
        if len(M_vals) >= 2:
            dM = abs(M_vals[-1] - M_vals[-2]) / max(abs(Mmax), 1e-6)
            if dM > 0.05:
                dphi = max(0.5 * dphi, dphi_min)
            elif dM < 0.01:
                dphi = min(1.2 * dphi, dphi_max)

        c_prev = ci
        phi_prev = phi
        phi += dphi

    return np.array(M_vals, dtype=float), np.array(phi_vals, dtype=float), np.array(c_vals, dtype=float)

def _f(datos, clave, default=None):
    valor = datos.get(clave, default)
    if valor is None or valor == "":
        raise ValueError(f"Falta el dato '{clave}'")
    return float(valor)


def _datos_h_mander_confinado(datos_hormigon, datos_acero, datos_seccion):
    fc0 = _f(datos_hormigon, "esfuerzo_fc")
    Ec  = _f(datos_hormigon, "modulo_Ec")
    ec0 = _f(datos_hormigon, "def_max_sin_confinar")
    esp = _f(datos_hormigon, "def_ultima_sin_confinar")

    fy  = _f(datos_acero, "esfuerzo_fy")
    fsu = _f(datos_acero, "esfuerzo_ultimo_acero")
    Es  = _f(datos_acero, "modulo_Es")
    ey  = _f(datos_acero, "def_fluencia_acero")
    esh = _f(datos_acero, "def_inicio_endurecimiento")
    esu = _f(datos_acero, "def_ultima_acero")

    b        = _f(datos_seccion, "disenar_columna_base")
    h        = _f(datos_seccion, "disenar_columna_altura")
    r        = _f(datos_seccion, "disenar_columna_recubrimiento")
    Sc       = _f(datos_seccion, "disenar_columna_espaciamiento")
    de       = _f(datos_seccion, "disenar_columna_diametro_transversal") / 10.0
    d_edge   = _f(datos_seccion, "disenar_columna_diametro_longitudinal_2") / 10.0
    d_corner = _f(datos_seccion, "disenar_columna_diametro_longitudinal_esq") / 10.0
    nl_x     = int(_f(datos_seccion, "disenar_columna_ramalesX"))
    nl_y     = int(_f(datos_seccion, "disenar_columna_ramalesY"))
    nb_x     = int(_f(datos_seccion, "disenar_columna_varillasX_2"))
    nb_y     = int(_f(datos_seccion, "disenar_columna_varillasY_2"))
    nb       = 2 * (nb_x - 2) + 2 * nb_y

    fyh = fy

    datos_h_base = (fyh, b, h, r, Sc, de, d_corner, d_edge, nb, nl_x, nl_y, None, None)

    fcc = mander_c(
        ec=np.array([0.0]),
        fc0=fc0,
        ec0=ec0,
        esp=esp,
        Ec=Ec,
        datos_h=datos_h_base,
        N=3,
    )

    datos_h_ecu = (fyh, b, h, r, Sc, de, d_corner, d_edge, nb, nl_x, nl_y, None, fcc)

    ecu = buscar_ecu(
        fc0=fc0,
        ec0=ec0,
        esp=esp,
        Ec=Ec,
        fy=fy,
        fsu=fsu,
        Es=Es,
        ey=ey,
        esh=esh,
        esu=esu,
        datos_h=datos_h_ecu,
    )

    return (fyh, b, h, r, Sc, de, d_corner, d_edge, nb, nl_x, nl_y, ecu, fcc)


def calcular_momento_curvatura(
    datos_hormigon,
    datos_acero,
    datos_seccion,
    datos_fibras,
    tipo_seccion,
    eje,
    modelo_cover,
    modelo_core,
    P=0.0,
    tol=1e-5,
):
    tipo = tipo_seccion.strip().lower()
    eje = eje.strip().lower()
    modelo_cover = modelo_cover.strip().lower()
    modelo_core = modelo_core.strip().lower()
    usa_mander_c = (modelo_cover == "mander_c" or modelo_core == "mander_c")

    # Materiales
    fc0 = _f(datos_hormigon, "esfuerzo_fc")
    Ec  = _f(datos_hormigon, "modulo_Ec")
    ec0 = _f(datos_hormigon, "def_max_sin_confinar")
    esp = _f(datos_hormigon, "def_ultima_sin_confinar")

    fy  = _f(datos_acero, "esfuerzo_fy")
    fsu = _f(datos_acero, "esfuerzo_ultimo_acero")
    Es  = _f(datos_acero, "modulo_Es")
    ey  = _f(datos_acero, "def_fluencia_acero")
    esh = _f(datos_acero, "def_inicio_endurecimiento")
    esu = _f(datos_acero, "def_ultima_acero")

    # Fibras
    nf_x = int(_f(datos_fibras, "fibras_x"))
    nf_y = int(_f(datos_fibras, "fibras_y"))

    # Modelos constitutivos
    sg_cover = sigma_hormigon(modelo_cover)
    sg_core = sigma_hormigon(modelo_core)

    datos_h = None

    if tipo == "columna":
        b        = _f(datos_seccion, "disenar_columna_base")
        h        = _f(datos_seccion, "disenar_columna_altura")
        r        = _f(datos_seccion, "disenar_columna_recubrimiento")
        de       = _f(datos_seccion, "disenar_columna_diametro_transversal") / 10.0
        nb_x     = int(_f(datos_seccion, "disenar_columna_varillasX_2"))
        nb_y     = int(_f(datos_seccion, "disenar_columna_varillasY_2"))
        d_edge   = _f(datos_seccion, "disenar_columna_diametro_longitudinal_2") / 10.0
        d_corner = _f(datos_seccion, "disenar_columna_diametro_longitudinal_esq") / 10.0

        cover, core = malla(b, h, r, de, nf_x, nf_y, eje)
        As = barras_columna(b, h, r, de, nb_x, nb_y, d_corner, d_edge, eje)

        P_real = _f(datos_seccion, "disenar_columna_axial", P)

        if usa_mander_c:
            datos_h = _datos_h_mander_confinado(datos_hormigon, datos_acero, datos_seccion)

    elif tipo == "viga":
        b      = _f(datos_seccion, "disenar_viga_base")
        h      = _f(datos_seccion, "disenar_viga_altura")
        r      = _f(datos_seccion, "disenar_viga_recubrimiento")
        de     = _f(datos_seccion, "disenar_viga_diametro_transversal") / 10.0
        nb_sup = int(_f(datos_seccion, "disenar_viga_varillas_superior"))
        nb_inf = int(_f(datos_seccion, "disenar_viga_varillas_inferior"))
        d_sup  = _f(datos_seccion, "disenar_viga_diametro_superior") / 10.0
        d_inf  = _f(datos_seccion, "disenar_viga_diametro_inferior") / 10.0

        cover, core = malla(b, h, r, de, nf_x, nf_y, "x")
        As = barras_viga(h, r, de, nb_sup, nb_inf, d_sup, d_inf)

        P_real = P

        if usa_mander_c:
            raise ValueError("Mander confinado no está habilitado para vigas en esta integración.")

    else:
        raise ValueError(f"Tipo de sección no válido: {tipo_seccion}")

    M, phi, c = diagrama_MC(
        cover, core, As, tol, h,
        fc0, ec0, esp, Ec,
        fy, fsu, Es, ey, esh, esu,
        P_real, datos_h, sg_cover, sg_core,
    )

    return phi * 100.0, M / 1e5, c


def calcular_series_mc(
    datos_hormigon,
    datos_acero,
    datos_seccion,
    datos_fibras,
    tipo_seccion,
    eje,
):
    tipo = tipo_seccion.strip().lower()

    series = {
        "hognestad": calcular_momento_curvatura(
            datos_hormigon, datos_acero, datos_seccion, datos_fibras,
            tipo, eje, "hognestad", "hognestad"
        )[:2],
        "mander_no_conf": calcular_momento_curvatura(
            datos_hormigon, datos_acero, datos_seccion, datos_fibras,
            tipo, eje, "mander_u", "mander_u"
        )[:2],
    }

    if tipo == "columna":
        series["mander_conf"] = calcular_momento_curvatura(
            datos_hormigon, datos_acero, datos_seccion, datos_fibras,
            tipo, eje, "mander_u", "mander_c"
        )[:2]

    return series